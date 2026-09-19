"""SpendGuard API request and response schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from spendguard.calculations import CalculationResult


Intent = Literal[
    "purchase",
    "recurring_cost",
    "finance_cost",
    "ownership_cost",
    "quote_audit",
    "budget_optimization",
    "unknown",
]


class AnalysisResult(BaseModel):
    """Structured baseline response returned by the agent."""

    intent: Intent
    summary: str = Field(min_length=1)
    known_facts: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    """Natural-language question submitted from the UI."""

    question: str = Field(min_length=1, max_length=4_000)


CalculationToolName = Literal[
    "calculate_installment",
    "calculate_refinance",
    "calculate_usage_cost",
    "annualize_expense",
    "calculate_tco",
    "compare_costs",
]


class CalculationRequest(BaseModel):
    """Existing calculation-tool request."""

    tool: CalculationToolName
    data: dict[str, Any]


class CalculationExecutionResult(BaseModel):
    """Calculation result with execution boundary."""

    tool: CalculationToolName
    execution: Literal["direct", "mcp"]
    calculation: CalculationResult
