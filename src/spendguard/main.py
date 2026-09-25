"""FastAPI application for SpendGuard decisions and deterministic tools."""

import asyncio
import json
import logging
import re
import tempfile
import time
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

from spendguard.codex_runtime import CodexRunner, CodexRuntimeError, CodexUsageLimitError
from spendguard.decision_state import DecisionDelta, extract_money_facts, persist_decision_result, update_state
from spendguard.calculations import (
    AnnualizedExpenseInput,
    CalculationResult,
    CostComparisonInput,
    InstallmentInput,
    RefinanceInput,
    RepeatedCostInput,
    SumCostsInput,
    TcoInput,
    UsageCostInput,
    annualize_expense,
    calculate_installment,
    calculate_refinance,
    calculate_repeated_cost,
    calculate_tco,
    calculate_usage_cost,
    compare_costs,
    sum_costs,
)
from spendguard.jev_judgments import JUDGMENTS
from spendguard.mcp_client import call_calculation_tool
from spendguard.models import CalculationExecutionResult, CalculationRequest, CalculationToolName


class DecisionTurn(BaseModel):
    question: str = Field(max_length=4000)
    answer: str = Field(max_length=12000)


class DecisionRequest(BaseModel):
    question: str = Field(max_length=4000)
    mode: Literal["baseline", "jev"] = "baseline"
    jev_candidate: Literal["subscription_audit", "quote_audit", "annual_leaks", "purchase_review"] | None = None
    candidate_text: str | None = None
    history: list[DecisionTurn] = Field(default_factory=list, max_length=6)
    request_id: UUID | None = None
    conversation_id: UUID | None = None


class DecisionResponse(BaseModel):
    status: Literal["ready"] = "ready"
    answer: str
    suggested_followups: list[str] = Field(default_factory=list, max_length=3)
    sources: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict


STATIC_DIR = Path(__file__).parent / "static"
logger = logging.getLogger("uvicorn.error")


class ProgressAccessFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        return not (
            isinstance(args, tuple)
            and len(args) >= 3
            and str(args[2]).startswith("/api/decisions/progress/")
        )


progress_access_filter = ProgressAccessFilter()

Calculator = Callable[[BaseModel], CalculationResult]

CALCULATION_TOOLS: dict[CalculationToolName, tuple[type[BaseModel], Calculator]] = {
    "calculate_installment": (InstallmentInput, calculate_installment),
    "calculate_refinance": (RefinanceInput, calculate_refinance),
    "calculate_usage_cost": (UsageCostInput, calculate_usage_cost),
    "calculate_repeated_cost": (RepeatedCostInput, calculate_repeated_cost),
    "sum_costs": (SumCostsInput, sum_costs),
    "annualize_expense": (AnnualizedExpenseInput, annualize_expense),
    "calculate_tco": (TcoInput, calculate_tco),
    "compare_costs": (CostComparisonInput, compare_costs),
}


def verify_calculation_trace(calls: list[dict]) -> int:
    """Recompute recorded MCP values before exposing a monetary answer."""

    checked = 0
    for call in calls:
        if call.get("tool") not in CALCULATION_TOOLS or call.get("status") != "completed":
            continue
        arguments = call.get("arguments") or {}
        actual_data = call.get("result")
        try:
            input_model, calculator = CALCULATION_TOOLS[call["tool"]]
            expected = calculator(input_model.model_validate(arguments["data"]))
            actual = CalculationResult.model_validate(actual_data)
        except (KeyError, TypeError, ValidationError) as error:
            raise CodexRuntimeError("Calculation result could not be verified.") from error
        try:
            result_matches = set(expected.result) == set(actual.result) and all(
                Decimal(str(actual.result[key])) == value if isinstance(value, Decimal)
                else actual.result[key] == value
                for key, value in expected.result.items()
            )
            intermediate_matches = set(expected.intermediate) == set(actual.intermediate) and all(
                Decimal(str(actual.intermediate[key])) == value
                for key, value in expected.intermediate.items()
            )
        except (InvalidOperation, ValueError) as error:
            raise CodexRuntimeError("Calculation result could not be verified.") from error
        if not result_matches or not intermediate_matches:
            raise CodexRuntimeError("Calculation result did not match deterministic inputs.")
        checked += 1
    return checked


def align_cashflow_claim(answer: str, composition: dict | None) -> tuple[str, bool]:
    """Replace a contradictory net-balance sentence with exact code arithmetic."""

    if not composition or "cashflow_after_fixed_expenses" not in composition:
        return answer, False
    expected = Decimal(str(composition["cashflow_after_fixed_expenses"]))
    pattern = re.compile(
        r"(?:내고 나면|지불하고 나면|지출 후|제외하면|빼면)[^.!?\n]{0,80}?([+-]?\d[\d,]*)\s*원"
    )
    sentences = re.split(r"(?<=[.!?])(?=\s|$)", answer)
    corrected = False
    for index, sentence in enumerate(sentences):
        match = pattern.search(sentence)
        if not match:
            continue
        claimed = Decimal(match[1].replace(",", ""))
        tail = sentence[match.end():]
        polarity_wrong = (expected < 0 and "남" in tail) or (expected > 0 and "부족" in tail)
        if claimed == abs(expected) and not polarity_wrong:
            continue
        amount = f"{abs(expected):,.0f}원"
        outcome = f"{amount}이 부족합니다." if expected < 0 else f"{amount}이 남습니다."
        leading = sentence[:len(sentence) - len(sentence.lstrip())]
        sentences[index] = leading + "현재 현금과 예정 수입에서 예정 고정지출을 빼면 " + outcome
        corrected = True
    return "".join(sentences), corrected


@asynccontextmanager
async def lifespan(app: FastAPI):
    runner = CodexRunner()
    await runner.check_authentication()
    app.state.codex_runner = runner
    app.state.decision_progress = {}
    app.state.decision_sessions = {}
    state_directory = tempfile.TemporaryDirectory(prefix="spendguard-states-")
    app.state.decision_state_dir = Path(state_directory.name)
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.addFilter(progress_access_filter)
    try:
        yield
    finally:
        access_logger.removeFilter(progress_access_filter)
        state_directory.cleanup()


app = FastAPI(title="SpendGuard", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Serve the SpendGuard UI."""

    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/api/decisions/progress/{request_id}")
async def decision_progress(request_id: UUID, request: Request) -> dict:
    """Return a small, user-facing progress snapshot for one request."""

    progress = request.app.state.decision_progress.get(str(request_id))
    if progress is None:
        raise HTTPException(status_code=404, detail="Decision progress unavailable.")
    return {
        "stage": progress["stage"],
        "elapsed_seconds": round(time.perf_counter() - progress["started_at"], 1),
        "search_calls": progress["search_calls"],
        "mcp_calls": progress["mcp_calls"],
    }


async def wait_for_disconnect(request: Request) -> None:
    while not await request.is_disconnected():
        await asyncio.sleep(0.5)


@app.post("/api/decisions", response_model=DecisionResponse)
async def decide(payload: DecisionRequest, request: Request) -> DecisionResponse:
    """Answer a question or continue a previous decision."""

    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="Question is required.")
    if payload.jev_candidate and payload.jev_candidate not in JUDGMENTS:
        raise HTTPException(status_code=422, detail="Unknown Jev candidate.")
    request_id = str(payload.request_id or uuid4())
    conversation_id = str(payload.conversation_id) if payload.conversation_id else None
    sessions = request.app.state.decision_sessions
    if conversation_id and conversation_id not in sessions:
        raise HTTPException(status_code=404, detail="Decision conversation unavailable.")
    previous_session = sessions.get(conversation_id) if conversation_id else None
    previous_thread = previous_session["thread_id"] if isinstance(previous_session, dict) else previous_session
    state_path = previous_session.get("state_path") if isinstance(previous_session, dict) else None
    if payload.mode == "jev" and state_path is None:
        state_dir = getattr(request.app.state, "decision_state_dir", Path(tempfile.gettempdir()) / "spendguard-codex-runtime" / "states")
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / f"{uuid4()}.json"
    started = time.perf_counter()
    progress = {"stage": "queued", "started_at": started, "search_calls": 0, "mcp_calls": 0}
    request.app.state.decision_progress[request_id] = progress
    logger.info("Decision %s received mode=%s history=%d", request_id, payload.mode, len(payload.history))

    def update_progress(stage: str) -> None:
        if stage == "search_completed":
            progress["search_calls"] += 1
            stage = "thinking"
        elif stage == "calculation_completed":
            progress["mcp_calls"] += 1
            stage = "thinking"
        if stage != progress["stage"] or stage == "thinking":
            progress["stage"] = stage
            logger.info(
                "Decision %s stage=%s elapsed=%.1fs search=%d mcp=%d",
                request_id, stage, time.perf_counter() - started,
                progress["search_calls"], progress["mcp_calls"],
            )

    async def log_heartbeat() -> None:
        while True:
            await asyncio.sleep(15)
            logger.info(
                "Decision %s running stage=%s elapsed=%.1fs search=%d mcp=%d",
                request_id, progress["stage"], time.perf_counter() - started,
                progress["search_calls"], progress["mcp_calls"],
            )

    heartbeat_task = asyncio.create_task(log_heartbeat())
    outcome = "failed"
    try:
        server_decision = None
        server_delta = None
        if payload.mode == "jev" and previous_thread and state_path and state_path.exists():
            parsed_facts = extract_money_facts(payload.question)
            if parsed_facts:
                previous_state = json.loads(state_path.read_text(encoding="utf-8"))
                changed_facts = {
                    name: value for name, value in parsed_facts.items()
                    if previous_state.get("judgment_facts", {}).get(name) != value
                }
                if changed_facts:
                    update_progress("thinking")
                    server_delta = DecisionDelta(judgment_facts=changed_facts)
                    server_decision = await asyncio.to_thread(update_state, state_path, server_delta)
                else:
                    server_decision = {
                        "composition": previous_state.get("composition", {}),
                        "jev_results": previous_state.get("jev_results", {}),
                        "update": {
                            "changed_keys": [], "jev_calls": 0, "new_judgments": [],
                            "reused_judgments": [name for name, item in previous_state.get("jev_results", {}).items()
                                                 if item.get("evaluated")],
                            "jev_latency_ms": 0, "transmitted_fields": {},
                        },
                    }
        codex_started = time.perf_counter()
        codex_task = asyncio.create_task(request.app.state.codex_runner.run(
            payload.question,
            history=[(turn.question, turn.answer) for turn in payload.history],
            thread_id=previous_thread,
            state_path=state_path,
            decision_mode=payload.mode,
            precomputed_decision=server_decision,
            on_progress=update_progress,
        ))
        disconnect_task = asyncio.create_task(wait_for_disconnect(request))
        try:
            done, _ = await asyncio.wait({codex_task, disconnect_task}, return_when=asyncio.FIRST_COMPLETED)
            if disconnect_task in done and codex_task not in done:
                outcome = "cancelled"
                raise HTTPException(status_code=499, detail="Decision request cancelled.")
            result = await codex_task
            verified_calculations = verify_calculation_trace(result.mcp_calls)
        finally:
            disconnect_task.cancel()
            if not codex_task.done():
                codex_task.cancel()
            await asyncio.gather(codex_task, disconnect_task, return_exceptions=True)
        prior_sources = previous_session.get("sources", []) if isinstance(previous_session, dict) else []
        response_sources = result.sources or prior_sources
        if previous_thread and prior_sources and not re.search(r"https?://", result.answer) and re.search(r"\d[\d,]*\s*원", result.answer):
            source = prior_sources[0]
            result.answer += f"\n\n기존 가격 출처: [{source['title'] or source['url']}]({source['url']})"
        if result.thread_id:
            conversation_id = conversation_id or str(uuid4())
            sessions[conversation_id] = {"thread_id": result.thread_id, "state_path": state_path, "sources": response_sources}
        completed_decision = next((call for call in reversed(result.mcp_calls)
                                   if call["tool"] == "update_decision_state" and call["status"] == "completed"), None)
        result.answer, cashflow_corrected = align_cashflow_claim(
            result.answer,
            server_decision.get("composition") if server_decision else
            completed_decision["result"].get("composition")
            if completed_decision and isinstance(completed_decision.get("result"), dict) else None,
        )
        if state_path and result.decision_delta and completed_decision and isinstance(completed_decision["result"], dict):
            persist_decision_result(
                state_path, DecisionDelta.model_validate(result.decision_delta), completed_decision["result"],
            )
        elif state_path and server_delta and server_decision:
            persist_decision_result(state_path, server_delta, server_decision)
        state_snapshot = json.loads(state_path.read_text(encoding="utf-8")) if state_path and state_path.exists() else None
        state_updated = any(call["tool"] == "update_decision_state" and call["status"] == "completed" for call in result.mcp_calls)
        jev_update = server_decision.get("update", {}) if server_decision else (
            state_snapshot.get("last_update", {}) if state_snapshot and state_updated else {}
        )
        jev_results = state_snapshot.get("jev_results", {}) if state_snapshot else {}
        logger.info(
            "Decision %s jev requests=%d judgments=%d reused=%d recomputed=%d state_changed=%s",
            request_id, jev_update.get("jev_calls", 0),
            sum(bool(item.get("evaluated")) for item in jev_results.values()),
            len(jev_update.get("reused_judgments", [])), len(jev_update.get("new_judgments", [])),
            bool(jev_update.get("changed_keys")),
        )
        outcome = "completed"
        return DecisionResponse(
            answer=result.answer,
            suggested_followups=result.suggested_followups,
            sources=response_sources,
            metadata={
                "request_id": request_id,
                "conversation_id": conversation_id,
                "resumed": result.resumed,
                "mode": payload.mode,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "first_visible_event_ms": (round((codex_started - started) * 1000) + result.first_visible_event_ms)
                if result.first_visible_event_ms is not None else None,
                "codex_thinking_ms": result.thinking_ms,
                "codex_runs": result.codex_runs,
                "codex_model_turns": result.model_turns,
                "search_calls": result.search_calls,
                "search_sources": result.search_sources,
                "mcp_calls": result.mcp_calls,
                "verified_calculations": verified_calculations,
                "cashflow_corrected": cashflow_corrected,
                "jev_calls": jev_update.get("jev_calls", 0),
                "jev_judgment_count": sum(bool(item.get("evaluated")) for item in jev_results.values()),
                "jev_new_judgments": jev_update.get("new_judgments", []),
                "jev_reused_judgments": jev_update.get(
                    "reused_judgments", [name for name, item in jev_results.items() if item.get("evaluated")]
                ),
                "jev_transmitted_fields": jev_update.get("transmitted_fields", {}),
                "jev_state_changed": bool(jev_update.get("changed_keys")),
                "jev_judgment": None,
            },
        )
    except CodexUsageLimitError as error:
        detail = {"code": "codex_usage_limit", "message": "현재 Codex 사용 한도에 도달했습니다. 초기화 후 다시 시도해 주세요."}
        if error.reset_at:
            detail["reset_at"] = error.reset_at
        raise HTTPException(status_code=429, detail=detail) from error
    except CodexRuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    finally:
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)
        progress["stage"] = outcome
        logger.info(
            "Decision %s %s elapsed=%.1fs search=%d mcp=%d",
            request_id, outcome, time.perf_counter() - started,
            progress["search_calls"], progress["mcp_calls"],
        )
        asyncio.get_running_loop().call_later(
            60, request.app.state.decision_progress.pop, request_id, None
        )


def run_calculation(payload: CalculationRequest) -> CalculationResult:
    """Existing Phase 3 calculation boundary."""

    input_model, calculator = CALCULATION_TOOLS[payload.tool]
    try:
        return calculator(input_model.model_validate(payload.data))
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=jsonable_encoder(error.errors())) from error


@app.post("/api/calculations/direct", response_model=CalculationExecutionResult)
async def calculate_direct(payload: CalculationRequest) -> CalculationExecutionResult:
    """Direct Phase 3 calculation result."""

    return CalculationExecutionResult(
        tool=payload.tool,
        execution="direct",
        calculation=run_calculation(payload),
    )


@app.post("/api/calculations/mcp", response_model=CalculationExecutionResult)
async def calculate_via_mcp(payload: CalculationRequest) -> CalculationExecutionResult:
    """Phase 4 stdio MCP calculation result."""

    try:
        calculation = await call_calculation_tool(payload.tool, payload.data)
        return CalculationExecutionResult(
            tool=payload.tool,
            execution="mcp",
            calculation=CalculationResult.model_validate(calculation),
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail="MCP calculation could not be completed.") from error
