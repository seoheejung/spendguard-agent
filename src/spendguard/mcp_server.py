"""Stdio MCP server for deterministic SpendGuard calculations."""

from fastmcp import FastMCP

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


if __name__ == "__main__":
    mcp.run()
