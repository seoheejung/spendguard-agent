from decimal import Decimal

import pytest
from pydantic import ValidationError

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


def test_installment_zero_rate_and_reproducibility() -> None:
    data = InstallmentInput(
        principal="1200",
        annual_interest_rate_pct="0",
        term_months=12,
        currency="USD",
    )

    first = calculate_installment(data)

    assert first == calculate_installment(data)
    assert first.result == {
        "monthly_payment": Decimal("100.00"),
        "total_payment": Decimal("1200.00"),
        "total_interest": Decimal("0.00"),
        "currency": "USD",
    }
    assert set(first.model_dump()) == {"inputs", "formula", "intermediate", "result"}


def test_installment_interest_and_rounding() -> None:
    result = calculate_installment(
        InstallmentInput(
            principal="1200",
            annual_interest_rate_pct="12",
            term_months=12,
            currency="USD",
        )
    )

    assert result.result["monthly_payment"] == Decimal("106.62")
    assert result.result["total_payment"] == Decimal("1279.44")
    assert result.result["total_interest"] == Decimal("79.44")


def test_installment_zero_principal() -> None:
    result = calculate_installment(
        InstallmentInput(
            principal="0",
            annual_interest_rate_pct="12",
            term_months=12,
            currency="KRW",
        )
    )

    assert result.result["monthly_payment"] == Decimal("0.00")


@pytest.mark.parametrize(
    ("input_data", "field"),
    [
        ({"principal": "-1", "annual_interest_rate_pct": "0", "term_months": 1, "currency": "KRW"}, "principal"),
        ({"principal": "1", "annual_interest_rate_pct": "-1", "term_months": 1, "currency": "KRW"}, "annual_interest_rate_pct"),
        ({"principal": "1", "annual_interest_rate_pct": "0", "term_months": 0, "currency": "KRW"}, "term_months"),
    ],
)
def test_installment_invalid_input_rejection(input_data: dict[str, object], field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        InstallmentInput.model_validate(input_data)


def test_refinance_includes_fee() -> None:
    result = calculate_refinance(
        RefinanceInput(
            remaining_principal="1200",
            current_annual_interest_rate_pct="0",
            current_remaining_months=12,
            new_annual_interest_rate_pct="0",
            new_term_months=12,
            refinancing_fee="100",
            currency="USD",
        )
    )

    assert result.result["new_remaining_total"] == Decimal("1300.00")
    assert result.result["savings"] == Decimal("-100.00")


def test_usage_cost_and_annualization() -> None:
    usage = calculate_usage_cost(UsageCostInput(total_cost="1", units="3", currency="USD"))
    annual = annualize_expense(AnnualizedExpenseInput(amount="10", period_months="3", currency="USD"))

    assert usage.result["cost_per_unit"] == Decimal("0.33")
    assert annual.result["annual_amount"] == Decimal("40.00")


def test_usage_and_annualization_boundaries() -> None:
    usage = calculate_usage_cost(UsageCostInput(total_cost="0", units="1", currency="KRW"))
    annual = annualize_expense(AnnualizedExpenseInput(amount="0", period_months="12", currency="KRW"))

    assert usage.result["cost_per_unit"] == Decimal("0.00")
    assert annual.result["annual_amount"] == Decimal("0.00")
    with pytest.raises(ValidationError, match="units"):
        UsageCostInput(total_cost="1", units="0", currency="KRW")
    with pytest.raises(ValidationError, match="period_months"):
        AnnualizedExpenseInput(amount="1", period_months="0", currency="KRW")


def test_tco_and_cost_comparison() -> None:
    tco = calculate_tco(
        TcoInput(
            purchase_cost="1000",
            monthly_ownership_cost="100",
            ownership_months=12,
            additional_cost="50",
            currency="USD",
        )
    )
    comparison = compare_costs(
        CostComparisonInput(
            options=[CostOption(name="standard", total_cost="100"), CostOption(name="discount", total_cost="80")],
            currency="USD",
        )
    )

    assert tco.result["tco"] == Decimal("2250.00")
    assert comparison.result["lowest_cost_option"] == "discount"
    assert comparison.result["difference_from_standard"] == Decimal("20.00")
    assert comparison.result["difference_from_discount"] == Decimal("0.00")
