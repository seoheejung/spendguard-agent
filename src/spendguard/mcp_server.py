"""Stdio MCP server for deterministic SpendGuard calculations."""

import os
from pathlib import Path

from fastmcp import FastMCP

from spendguard.decision_state import DecisionDelta, update_state

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
    annualize_expense as annualize_expense_calculation,
    calculate_installment as calculate_installment_calculation,
    calculate_refinance as calculate_refinance_calculation,
    calculate_repeated_cost as calculate_repeated_cost_calculation,
    calculate_tco as calculate_tco_calculation,
    calculate_usage_cost as calculate_usage_cost_calculation,
    compare_costs as compare_costs_calculation,
    sum_costs as sum_costs_calculation,
)


mcp = FastMCP("SpendGuard Calculation Tools")


@mcp.tool(annotations={"readOnlyHint": True})
def calculate_installment(data: InstallmentInput) -> CalculationResult:
    """Installment cost calculation."""

    return calculate_installment_calculation(data)


@mcp.tool(annotations={"readOnlyHint": True})
def calculate_refinance(data: RefinanceInput) -> CalculationResult:
    """Refinance cost calculation."""

    return calculate_refinance_calculation(data)


@mcp.tool(annotations={"readOnlyHint": True})
def calculate_usage_cost(data: UsageCostInput) -> CalculationResult:
    """Usage-cost calculation."""

    return calculate_usage_cost_calculation(data)


@mcp.tool(annotations={"readOnlyHint": True})
def calculate_repeated_cost(data: RepeatedCostInput) -> CalculationResult:
    """Multiply a sourced unit price by an explicit quantity with its unit."""

    return calculate_repeated_cost_calculation(data)


@mcp.tool(annotations={"readOnlyHint": True})
def sum_costs(data: SumCostsInput) -> CalculationResult:
    """Sum cost items once and optionally subtract them from a budget."""

    return sum_costs_calculation(data)


@mcp.tool(annotations={"readOnlyHint": True})
def annualize_expense(data: AnnualizedExpenseInput) -> CalculationResult:
    """Annualized expense calculation."""

    return annualize_expense_calculation(data)


@mcp.tool(annotations={"readOnlyHint": True})
def calculate_tco(data: TcoInput) -> CalculationResult:
    """Total-cost-of-ownership calculation."""

    return calculate_tco_calculation(data)


@mcp.tool(annotations={"readOnlyHint": True})
def compare_costs(data: CostComparisonInput) -> CalculationResult:
    """Cost-option comparison."""

    return compare_costs_calculation(data)


@mcp.tool(annotations={"readOnlyHint": True})
def update_decision_state(delta: DecisionDelta) -> dict:
    """Evaluate a purchase decision from this turn's evidence and prior local state. For judgment_facts use only explicit normalized values: age in months, functional status, approved problem and feature tags, cash amounts, prices, budget, and wait duration. Return judgments only; FastAPI stores session state."""

    path = os.environ.get("SPENDGUARD_STATE_PATH")
    if not path:
        raise RuntimeError("Decision state unavailable.")
    return update_state(Path(path), delta)


if __name__ == "__main__":
    mcp.run()
