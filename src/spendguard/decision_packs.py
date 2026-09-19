"""Phase 6 decision-pack workflow using existing research and MCP tools."""

from collections.abc import Awaitable, Callable
from typing import Any

from spendguard.mcp_client import call_calculation_tool
from spendguard.models import AnalysisResult, CalculationExecutionResult, DecisionPackResult


PACK_BY_INTENT = {
    "purchase": "purchase",
    "recurring_cost": "recurring_cost",
    "finance_cost": "finance_cost",
    "ownership_cost": "ownership_cost",
    "quote_audit": "quote_audit",
    "budget_optimization": "budget_optimization",
}

REQUIRED_FIELDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "purchase": (("target",), ("purpose",), ("price", "price_confirmation_needed")),
    "recurring_cost": (("item",), ("current_cost",)),
    "finance_cost": (("amount",), ("term_months",), ("rate_or_comparison",)),
    "ownership_cost": (("target",), ("ownership_months",)),
    "quote_audit": (("quote_items",),),
    "budget_optimization": (("budget", "expenses"),),
}

McpCaller = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


def pack_for_analysis(analysis: AnalysisResult) -> str | None:
    """Map a validated intent to its only supported decision pack."""

    return PACK_BY_INTENT.get(analysis.intent)


def missing_required_fields(pack: str, data: dict[str, Any]) -> list[str]:
    """Check code-owned required data without deriving or guessing a value."""

    missing: list[str] = []
    for alternatives in REQUIRED_FIELDS[pack]:
        if any(data.get(field) not in (None, "", [], {}) for field in alternatives):
            continue
        missing.append(" or ".join(alternatives))
    return missing


def _calculation_requests(pack: str, data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Select existing calculation tools only when their explicit inputs exist."""

    currency = data.get("currency", "KRW")
    options = data.get("options")
    requests: list[tuple[str, dict[str, Any]]] = []
    if isinstance(options, list) and len(options) >= 2:
        requests.append(("compare_costs", {"options": options, "currency": currency}))

    if pack == "purchase" and all(key in data for key in ("total_cost", "units")):
        requests.append(
            ("calculate_usage_cost", {"total_cost": data["total_cost"], "units": data["units"], "currency": currency})
        )
    elif pack == "recurring_cost" and all(key in data for key in ("current_cost", "period_months")):
        requests.append(
            ("annualize_expense", {"amount": data["current_cost"], "period_months": data["period_months"], "currency": currency})
        )
    elif pack == "finance_cost":
        refinance_keys = {
            "remaining_principal",
            "current_annual_interest_rate_pct",
            "current_remaining_months",
            "new_annual_interest_rate_pct",
            "new_term_months",
            "refinancing_fee",
        }
        if refinance_keys <= data.keys():
            requests.append(("calculate_refinance", {key: data[key] for key in refinance_keys} | {"currency": currency}))
        elif all(key in data for key in ("principal", "annual_interest_rate_pct", "term_months")):
            requests.append(
                (
                    "calculate_installment",
                    {
                        "principal": data["principal"],
                        "annual_interest_rate_pct": data["annual_interest_rate_pct"],
                        "term_months": data["term_months"],
                        "currency": currency,
                    },
                )
            )
    elif pack == "ownership_cost" and all(
        key in data for key in ("purchase_cost", "monthly_ownership_cost", "ownership_months", "additional_cost")
    ):
        requests.append(
            (
                "calculate_tco",
                {
                    "purchase_cost": data["purchase_cost"],
                    "monthly_ownership_cost": data["monthly_ownership_cost"],
                    "ownership_months": data["ownership_months"],
                    "additional_cost": data["additional_cost"],
                    "currency": currency,
                },
            )
        )
    elif pack == "budget_optimization" and all(key in data for key in ("amount", "period_months")):
        requests.append(
            ("annualize_expense", {"amount": data["amount"], "period_months": data["period_months"], "currency": currency})
        )
    return requests


def _option_names(data: dict[str, Any]) -> list[str]:
    """Expose only user-provided option labels."""

    options = data.get("options")
    if not isinstance(options, list):
        return []
    return [str(option["name"]) for option in options if isinstance(option, dict) and option.get("name")]


async def build_decision_pack(
    analysis: AnalysisResult,
    data: dict[str, Any],
    *,
    mcp_caller: McpCaller = call_calculation_tool,
) -> DecisionPackResult:
    """Produce a traceable decision result without side effects or invented facts."""

    pack = pack_for_analysis(analysis)
    if pack is None:
        return DecisionPackResult(
            pack=None,
            status="needs_input",
            conclusion="A Decision Pack could not be identified from this request.",
            facts=analysis.known_facts,
            assumptions=analysis.assumptions,
            missing_fields=["decision pack context"],
            risks=["The request is ambiguous, so no pack workflow or tool was run."],
            next_actions=["Provide the spending target and the decision you want to compare."],
            sources=analysis.external_facts,
        )

    missing = missing_required_fields(pack, data)
    if missing:
        return DecisionPackResult(
            pack=pack,
            status="needs_input",
            conclusion="Required information is incomplete; no calculation or purchase conclusion was made.",
            facts=analysis.known_facts,
            assumptions=analysis.assumptions,
            missing_fields=missing,
            risks=["Missing inputs prevent a verified comparison."],
            next_actions=[f"Provide: {field}" for field in missing],
            sources=analysis.external_facts,
        )

    calculations: list[CalculationExecutionResult] = []
    try:
        for tool, calculation_data in _calculation_requests(pack, data):
            calculation = await mcp_caller(tool, calculation_data)
            calculations.append(
                CalculationExecutionResult(
                    tool=tool,
                    execution="mcp",
                    calculation=calculation,
                )
            )
    except Exception:
        return DecisionPackResult(
            pack=pack,
            status="tool_error",
            conclusion="A required calculation tool could not be completed, so no decision was confirmed.",
            facts=analysis.known_facts,
            assumptions=analysis.assumptions,
            options=_option_names(data),
            risks=["Calculation evidence is unavailable."],
            next_actions=["Review the calculation inputs and retry."],
            sources=analysis.external_facts,
        )

    risks: list[str] = []
    if analysis.research.needed and analysis.research.status != "completed":
        risks.append(analysis.research.note)
    return DecisionPackResult(
        pack=pack,
        status="ready",
        conclusion=analysis.summary,
        facts=analysis.known_facts,
        assumptions=analysis.assumptions,
        calculations=calculations,
        options=_option_names(data),
        risks=risks,
        next_actions=["Review the facts, assumptions, calculations, and sources before acting."],
        sources=analysis.external_facts,
    )
