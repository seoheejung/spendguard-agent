"""FastAPI application for SpendGuard decisions and deterministic tools."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

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


class DecisionRequest(BaseModel):
    question: str
    mode: Literal["baseline", "jev"] = "baseline"
    jev_candidate: Literal["subscription_audit", "quote_audit", "annual_leaks", "purchase_review"] | None = None
    candidate_text: str | None = None


class DecisionResponse(BaseModel):
    status: Literal["ready"] = "ready"
    answer: str
    metadata: dict


STATIC_DIR = Path(__file__).parent / "static"

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
    yield


app = FastAPI(title="SpendGuard", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Serve the SpendGuard UI."""

    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})


@app.post("/api/decisions", response_model=DecisionResponse)
async def decide(payload: DecisionRequest, request: Request) -> DecisionResponse:
    """Answer a question in one isolated Codex turn."""

    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="Question is required.")
    if payload.jev_candidate and payload.jev_candidate not in JUDGMENTS:
        raise HTTPException(status_code=422, detail="Unknown Jev candidate.")
    try:
        jev = None
        if payload.mode == "jev" and payload.jev_candidate:
            jev = await judge_candidate(
                payload.jev_candidate, payload.question, payload.candidate_text or payload.question
            )
        result = await request.app.state.codex_runner.run(
            payload.question,
            jev_context=jev.as_prompt() if jev else "",
        )
        return DecisionResponse(
            answer=result.answer,
            metadata={
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
