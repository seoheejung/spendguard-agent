"""Deterministic Phase 3 cost calculations."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

from pydantic import BaseModel, Field, WithJsonSchema


MONEY_QUANTUM = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    """Fixed currency rounding."""

    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


class CalculationResult(BaseModel):
    """Traceable calculation output."""

    inputs: dict[str, object]
    formula: str
    intermediate: dict[str, Decimal]
    result: dict[str, Decimal | str]


class InstallmentInput(BaseModel):
    """Installment calculation input."""

    principal: Decimal = Field(ge=0)
    annual_interest_rate_pct: Decimal = Field(ge=0)
    term_months: int = Field(gt=0)
    currency: str = Field(min_length=1)


class RefinanceInput(BaseModel):
    """Refinance comparison input."""

    remaining_principal: Decimal = Field(ge=0)
    current_annual_interest_rate_pct: Decimal = Field(ge=0)
    current_remaining_months: int = Field(gt=0)
    new_annual_interest_rate_pct: Decimal = Field(ge=0)
    new_term_months: int = Field(gt=0)
    refinancing_fee: Decimal = Field(ge=0)
    currency: str = Field(min_length=1)


class UsageCostInput(BaseModel):
    """Usage-cost calculation input."""

    total_cost: Decimal = Field(ge=0)
    units: Decimal = Field(gt=0)
    currency: str = Field(min_length=1)


class RepeatedCostInput(BaseModel):
    """Unit price and quantity input."""

    unit_cost: Decimal = Field(ge=0)
    quantity: Decimal = Field(ge=0)
    unit: str = Field(min_length=1)
    currency: str = Field(min_length=1)


class CostLine(BaseModel):
    name: str = Field(min_length=1)
    amount: Decimal = Field(ge=0)


class SumCostsInput(BaseModel):
    """Several cost lines and an optional budget."""

    items: list[CostLine] = Field(min_length=1)
    budget: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(min_length=1)


class AnnualizedExpenseInput(BaseModel):
    """Period-expense annualization input."""

    amount: Decimal = Field(ge=0)
    period_months: Decimal = Field(gt=0)
    currency: str = Field(min_length=1)


class TcoInput(BaseModel):
    """Total-cost-of-ownership input."""

    purchase_cost: Decimal = Field(ge=0)
    monthly_ownership_cost: Decimal = Field(ge=0)
    ownership_months: int = Field(gt=0)
    additional_cost: Decimal = Field(ge=0)
    currency: str = Field(min_length=1)


class CostOption(BaseModel):
    """Comparable option cost."""

    name: str = Field(min_length=1)
    total_cost: Annotated[
        Decimal, WithJsonSchema({"type": "number"}, mode="validation")
    ] = Field(ge=0)


class CostComparisonInput(BaseModel):
    """Cost-option comparison input."""

    options: list[CostOption] = Field(min_length=2)
    currency: str = Field(min_length=1)


def calculate_installment(data: InstallmentInput) -> CalculationResult:
    """Amortizing monthly installment calculation."""

    monthly_rate = data.annual_interest_rate_pct / Decimal("1200")
    if data.principal == 0:
        monthly_payment = Decimal("0")
    elif monthly_rate == 0:
        monthly_payment = data.principal / data.term_months
    else:
        factor = (Decimal("1") + monthly_rate) ** data.term_months
        monthly_payment = data.principal * monthly_rate * factor / (factor - Decimal("1"))

    monthly_payment = _money(monthly_payment)
    total_payment = _money(monthly_payment * data.term_months)
    total_interest = _money(total_payment - data.principal)
    return CalculationResult(
        inputs=data.model_dump(),
        formula="monthly_payment = P*r*(1+r)^n / ((1+r)^n-1); r = annual_rate / 1200",
        intermediate={"monthly_rate": monthly_rate, "term_months": Decimal(data.term_months)},
        result={
            "monthly_payment": monthly_payment,
            "total_payment": total_payment,
            "total_interest": total_interest,
            "currency": data.currency,
        },
    )


def calculate_refinance(data: RefinanceInput) -> CalculationResult:
    """Remaining-cost refinance comparison."""

    current = calculate_installment(
        InstallmentInput(
            principal=data.remaining_principal,
            annual_interest_rate_pct=data.current_annual_interest_rate_pct,
            term_months=data.current_remaining_months,
            currency=data.currency,
        )
    )
    replacement = calculate_installment(
        InstallmentInput(
            principal=data.remaining_principal,
            annual_interest_rate_pct=data.new_annual_interest_rate_pct,
            term_months=data.new_term_months,
            currency=data.currency,
        )
    )
    current_total = current.result["total_payment"]
    new_total_before_fee = replacement.result["total_payment"]
    assert isinstance(current_total, Decimal)
    assert isinstance(new_total_before_fee, Decimal)
    new_total = _money(new_total_before_fee + data.refinancing_fee)
    savings = _money(current_total - new_total)
    return CalculationResult(
        inputs=data.model_dump(),
        formula="savings = current_remaining_total - (new_remaining_total + refinancing_fee)",
        intermediate={
            "current_monthly_payment": current.result["monthly_payment"],
            "new_monthly_payment": replacement.result["monthly_payment"],
            "current_remaining_total": current_total,
            "new_remaining_total_before_fee": new_total_before_fee,
        },
        result={
            "new_remaining_total": new_total,
            "savings": savings,
            "currency": data.currency,
        },
    )


def calculate_usage_cost(data: UsageCostInput) -> CalculationResult:
    """Cost-per-unit calculation."""

    cost_per_unit = _money(data.total_cost / data.units)
    return CalculationResult(
        inputs=data.model_dump(),
        formula="cost_per_unit = total_cost / units",
        intermediate={"units": data.units},
        result={"cost_per_unit": cost_per_unit, "currency": data.currency},
    )


def calculate_repeated_cost(data: RepeatedCostInput) -> CalculationResult:
    """Total cost for a quantity of identical units."""

    total = _money(data.unit_cost * data.quantity)
    return CalculationResult(
        inputs=data.model_dump(),
        formula="total_cost = unit_cost * quantity",
        intermediate={"quantity": data.quantity},
        result={"total_cost": total, "currency": data.currency},
    )


def sum_costs(data: SumCostsInput) -> CalculationResult:
    """One-pass cost total and remaining budget."""

    total = _money(sum((item.amount for item in data.items), Decimal("0")))
    result: dict[str, Decimal | str] = {"total_cost": total, "currency": data.currency}
    if data.budget is not None:
        result["budget_remaining"] = _money(data.budget - total)
    return CalculationResult(
        inputs=data.model_dump(),
        formula="total_cost = sum(item.amount); budget_remaining = budget - total_cost",
        intermediate={item.name: item.amount for item in data.items},
        result=result,
    )


def annualize_expense(data: AnnualizedExpenseInput) -> CalculationResult:
    """Annual-equivalent expense calculation."""

    multiplier = Decimal("12") / data.period_months
    annual_amount = _money(data.amount * multiplier)
    return CalculationResult(
        inputs=data.model_dump(),
        formula="annual_amount = amount * (12 / period_months)",
        intermediate={"annualization_multiplier": multiplier},
        result={"annual_amount": annual_amount, "currency": data.currency},
    )


def calculate_tco(data: TcoInput) -> CalculationResult:
    """Total-cost-of-ownership calculation."""

    recurring_total = _money(data.monthly_ownership_cost * data.ownership_months)
    total_cost = _money(data.purchase_cost + recurring_total + data.additional_cost)
    return CalculationResult(
        inputs=data.model_dump(),
        formula="tco = purchase_cost + (monthly_ownership_cost * ownership_months) + additional_cost",
        intermediate={"recurring_total": recurring_total},
        result={"tco": total_cost, "currency": data.currency},
    )


def compare_costs(data: CostComparisonInput) -> CalculationResult:
    """Lowest-cost option comparison."""

    lowest = min(data.options, key=lambda option: option.total_cost)
    differences = {
        f"difference_from_{option.name}": _money(option.total_cost - lowest.total_cost)
        for option in data.options
    }
    return CalculationResult(
        inputs=data.model_dump(),
        formula="difference_from_lowest = option_total_cost - lowest_total_cost",
        intermediate={option.name: option.total_cost for option in data.options},
        result={
            "lowest_cost_option": lowest.name,
            "lowest_total_cost": _money(lowest.total_cost),
            "currency": data.currency,
            **differences,
        },
    )
