"""Phase 4 MCP server integration tests."""

import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from spendguard.calculations import (
    AnnualizedExpenseInput,
    CostComparisonInput,
    CostOption,
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
from spendguard.mcp_client import call_calculation_tool, list_calculation_tools
from spendguard.mcp_server import mcp


EXPECTED_TOOLS = {
    "calculate_installment",
    "calculate_refinance",
    "calculate_usage_cost",
    "calculate_repeated_cost",
    "sum_costs",
    "annualize_expense",
    "calculate_tco",
    "compare_costs",
}


def _mcp_data(result: object) -> dict[str, object]:
    assert isinstance(result, dict)
    return result


def test_mcp_server_lists_all_calculation_tools() -> None:
    assert set(asyncio.run(list_calculation_tools())) == EXPECTED_TOOLS


@pytest.mark.parametrize(
    ("name", "data", "direct_result"),
    [
        (
            "calculate_installment",
            {"principal": "1200", "annual_interest_rate_pct": "12", "term_months": 12, "currency": "USD"},
            calculate_installment(
                InstallmentInput(principal="1200", annual_interest_rate_pct="12", term_months=12, currency="USD")
            ),
        ),
        (
            "calculate_refinance",
            {
                "remaining_principal": "1200",
                "current_annual_interest_rate_pct": "12",
                "current_remaining_months": 12,
                "new_annual_interest_rate_pct": "6",
                "new_term_months": 12,
                "refinancing_fee": "10",
                "currency": "USD",
            },
            calculate_refinance(
                RefinanceInput(
                    remaining_principal="1200",
                    current_annual_interest_rate_pct="12",
                    current_remaining_months=12,
                    new_annual_interest_rate_pct="6",
                    new_term_months=12,
                    refinancing_fee="10",
                    currency="USD",
                )
            ),
        ),
        (
            "calculate_usage_cost",
            {"total_cost": "10", "units": "3", "currency": "USD"},
            calculate_usage_cost(UsageCostInput(total_cost="10", units="3", currency="USD")),
        ),
        (
            "annualize_expense",
            {"amount": "10", "period_months": "3", "currency": "USD"},
            annualize_expense(AnnualizedExpenseInput(amount="10", period_months="3", currency="USD")),
        ),
        (
            "calculate_tco",
            {
                "purchase_cost": "1000",
                "monthly_ownership_cost": "100",
                "ownership_months": 12,
                "additional_cost": "50",
                "currency": "USD",
            },
            calculate_tco(
                TcoInput(
                    purchase_cost="1000",
                    monthly_ownership_cost="100",
                    ownership_months=12,
                    additional_cost="50",
                    currency="USD",
                )
            ),
        ),
        (
            "compare_costs",
            {
                "options": [
                    {"name": "standard", "total_cost": "100"},
                    {"name": "discount", "total_cost": "80"},
                ],
                "currency": "USD",
            },
            compare_costs(
                CostComparisonInput(
                    options=[CostOption(name="standard", total_cost="100"), CostOption(name="discount", total_cost="80")],
                    currency="USD",
                )
            ),
        ),
    ],
)
def test_mcp_tool_matches_direct_calculation(name: str, data: dict[str, object], direct_result: object) -> None:
    mcp_result = _mcp_data(asyncio.run(call_calculation_tool(name, data)))
    assert hasattr(direct_result, "model_dump")
    assert mcp_result == direct_result.model_dump(mode="json")


def test_mcp_input_validation_error() -> None:
    async def call_invalid_tool() -> None:
        async with Client(mcp) as client:
            await client.call_tool(
                "calculate_usage_cost",
                {"data": {"total_cost": "1", "units": "0", "currency": "USD"}},
            )

    with pytest.raises(ToolError):
        asyncio.run(call_invalid_tool())


def test_mcp_output_schema_contains_traceability_fields() -> None:
    async def output_schema() -> dict[str, object]:
        async with Client(mcp) as client:
            tools = await client.list_tools()
        tool = next(item for item in tools if item.name == "calculate_installment")
        return tool.output_schema

    schema = asyncio.run(output_schema())
    assert set(schema["properties"]) == {"inputs", "formula", "intermediate", "result"}
