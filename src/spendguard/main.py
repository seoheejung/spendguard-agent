"""FastAPI application for SpendGuard decisions and deterministic tools."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

from spendguard.codex_runtime import CodexRunner, CodexRuntimeError
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
from spendguard.jev_judgments import JUDGMENTS, JevError, judge_candidate
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


class DecisionResponse(BaseModel):
    status: Literal["ready"] = "ready"
    answer: str
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    runner = CodexRunner()
    await runner.check_authentication()
    app.state.codex_runner = runner
    app.state.decision_progress = {}
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.addFilter(progress_access_filter)
    try:
        yield
    finally:
        access_logger.removeFilter(progress_access_filter)


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
    }


async def wait_for_disconnect(request: Request) -> None:
    while not await request.is_disconnected():
        await asyncio.sleep(0.5)


@app.post("/api/decisions", response_model=DecisionResponse)
async def decide(payload: DecisionRequest, request: Request) -> DecisionResponse:
    """Answer a question in one isolated Codex turn."""

    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="Question is required.")
    if payload.jev_candidate and payload.jev_candidate not in JUDGMENTS:
        raise HTTPException(status_code=422, detail="Unknown Jev candidate.")
    request_id = str(payload.request_id or uuid4())
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
        jev = None
        if payload.mode == "jev" and payload.jev_candidate:
            update_progress("thinking")
            jev = await judge_candidate(
                payload.jev_candidate, payload.question, payload.candidate_text or payload.question
            )
        codex_task = asyncio.create_task(request.app.state.codex_runner.run(
            payload.question,
            jev_context=jev.as_prompt() if jev else "",
            history=[(turn.question, turn.answer) for turn in payload.history],
            on_progress=update_progress,
        ))
        disconnect_task = asyncio.create_task(wait_for_disconnect(request))
        try:
            done, _ = await asyncio.wait({codex_task, disconnect_task}, return_when=asyncio.FIRST_COMPLETED)
            if disconnect_task in done and codex_task not in done:
                outcome = "cancelled"
                raise HTTPException(status_code=499, detail="Decision request cancelled.")
            result = await codex_task
        finally:
            disconnect_task.cancel()
            if not codex_task.done():
                codex_task.cancel()
            await asyncio.gather(codex_task, disconnect_task, return_exceptions=True)
        outcome = "completed"
        return DecisionResponse(
            answer=result.answer,
            metadata={
                "request_id": request_id,
                "mode": payload.mode,
                "latency_ms": result.latency_ms + (jev.latency_ms if jev else 0),
                "codex_runs": result.codex_runs,
                "search_calls": result.search_calls,
                "search_sources": result.search_sources,
                "mcp_calls": result.mcp_calls,
                "jev_calls": 1 if jev else 0,
                "jev_judgment": jev.as_metadata() if jev else None,
            },
        )
    except JevError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
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
