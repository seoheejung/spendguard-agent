"""FastAPI application for the SpendGuard Phase 1 baseline."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Protocol

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from spendguard.agent import (
    AgentConfigurationError,
    AgentExecutionError,
    OpenAIAnalyzer,
    ResearchExecutionError,
    needs_current_information,
)
from spendguard.calculations import (
    AnnualizedExpenseInput,
    CalculationResult,
    CostComparisonInput,
    InstallmentInput,
    RefinanceInput,
    TcoInput,
    UsageCostInput,
    annualize_expense,
    calculate_installment,
    calculate_refinance,
    calculate_tco,
    calculate_usage_cost,
    compare_costs,
)
from spendguard.mcp_client import call_calculation_tool
from spendguard.models import (
    AnalysisResult,
    AnalyzeRequest,
    CalculationExecutionResult,
    CalculationRequest,
    CalculationToolName,
    ResearchNeed,
)


class Analyzer(Protocol):
    """Minimal analyzer interface for the API boundary."""

    async def analyze(self, question: str) -> AnalysisResult: ...


STATIC_DIR = Path(__file__).parent / "static"

Calculator = Callable[[BaseModel], CalculationResult]

CALCULATION_TOOLS: dict[CalculationToolName, tuple[type[BaseModel], Calculator]] = {
    "calculate_installment": (InstallmentInput, calculate_installment),
    "calculate_refinance": (RefinanceInput, calculate_refinance),
    "calculate_usage_cost": (UsageCostInput, calculate_usage_cost),
    "annualize_expense": (AnnualizedExpenseInput, annualize_expense),
    "calculate_tco": (TcoInput, calculate_tco),
    "compare_costs": (CostComparisonInput, compare_costs),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.analyzer = OpenAIAnalyzer()
    yield


app = FastAPI(title="SpendGuard", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Serve the Phase 1 UI."""

    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze(payload: AnalyzeRequest, request: Request) -> AnalysisResult:
    """Analyze a natural-language question with the configured single agent."""

    analyzer: Analyzer = request.app.state.analyzer
    try:
        return await analyzer.analyze(payload.question)
    except AgentConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ResearchExecutionError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except AgentExecutionError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/research-needed", response_model=ResearchNeed)
async def research_needed(payload: AnalyzeRequest) -> ResearchNeed:
    """Expose the backend-owned Phase 5 search decision to the workspace."""

    return ResearchNeed(needed=needs_current_information(payload.question))


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
