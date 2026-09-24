"""Public request and response types for deterministic calculation endpoints."""

from typing import Any, Literal

from pydantic import BaseModel

from spendguard.calculations import CalculationResult


CalculationToolName = Literal[
    "calculate_installment",
    "calculate_refinance",
    "calculate_usage_cost",
    "calculate_repeated_cost",
    "sum_costs",
    "annualize_expense",
    "calculate_tco",
    "compare_costs",
]


class CalculationRequest(BaseModel):
    tool: CalculationToolName
    data: dict[str, Any]


class CalculationExecutionResult(BaseModel):
    tool: CalculationToolName
    execution: Literal["direct", "mcp"]
    calculation: CalculationResult
