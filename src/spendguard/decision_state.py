"""Local decision state and minimum-input Jev bundle."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

from spendguard.jev_judgments import JevError, _load_key


STATE_FIELDS = (
    "user_facts", "assumptions", "current_facts", "alternatives",
    "calculations", "jev_results", "sources",
)


class DecisionDelta(BaseModel):
    """Local additions to a decision session."""

    user_facts: dict[str, Any] = Field(default_factory=dict)
    assumptions: dict[str, Any] = Field(default_factory=dict)
    current_facts: dict[str, Any] = Field(default_factory=dict)
    alternatives: dict[str, Any] = Field(default_factory=dict)
    calculations: dict[str, Any] = Field(default_factory=dict)
    sources: dict[str, str] = Field(default_factory=dict)
    judgment_facts: "JudgmentFacts" = Field(default_factory=lambda: JudgmentFacts())


class JudgmentFacts(BaseModel):
    """Allowlisted normalized facts, never a raw question or personal identifier."""

    current_product_age_months: int | None = None
    current_product_functional: bool | None = None
    reported_problems: list[str] | None = None
    requested_upgrade_features: list[str] | None = None
    usage_frequency: str | None = None
    available_cash: float | None = None
    purchase_price: float | None = None
    upcoming_fixed_expense: float | None = None
    upcoming_income: float | None = None
    alternative_price: float | None = None
    budget: float | None = None
    can_wait_months: float | None = None


FIELD_TYPES: dict[str, type | set[str]] = {
    "current_product_age_months": int,
    "current_product_functional": bool,
    "reported_problems": {"battery", "connection", "damage", "fit", "sound", "none", "other"},
    "requested_upgrade_features": {"noise_cancellation", "wireless_charging", "battery", "sound", "fit", "other"},
    "usage_frequency": {"daily", "weekly", "rarely", "unknown"},
    "available_cash": (int, float),
    "purchase_price": (int, float),
    "upcoming_fixed_expense": (int, float),
    "upcoming_income": (int, float),
    "alternative_price": (int, float),
    "budget": (int, float),
    "can_wait_months": (int, float),
}

JUDGMENTS: dict[str, tuple[str, tuple[str, ...], str]] = {
    "replacement_needed": ("noul", ("current_product_age_months", "current_product_functional", "reported_problems"), "Is immediate replacement necessary given the current item's condition?"),
    "cashflow_harmed": ("noul", ("available_cash", "purchase_price", "upcoming_fixed_expense", "upcoming_income", "budget"), "Would this purchase materially harm available living-expense cashflow?"),
    "waiting_low_loss": ("noul", ("current_product_functional", "reported_problems", "can_wait_months"), "Would delaying the purchase have little practical cost?"),
    "replacement_need_score": ("score", ("current_product_age_months", "current_product_functional", "reported_problems", "usage_frequency"), "How strong is the current item's replacement need?"),
    "purchase_burden_score": ("score", ("available_cash", "purchase_price", "upcoming_fixed_expense", "upcoming_income", "budget"), "How burdensome is this purchase?"),
    "upgrade_value_score": ("score", ("reported_problems", "requested_upgrade_features", "usage_frequency", "purchase_price"), "How valuable are the upgrade features for the stated usage?"),
    "purchase_choice": ("choice", ("current_product_functional", "reported_problems", "available_cash", "purchase_price", "upcoming_fixed_expense", "upcoming_income", "alternative_price", "budget", "can_wait_months"), "Which purchase action best fits the supplied facts?"),
    "key_factor": ("factor", ("reported_problems", "requested_upgrade_features", "available_cash", "purchase_price", "upcoming_fixed_expense", "alternative_price", "budget"), "What is the main purchase decision factor?"),
}

MONEY_AMOUNT = re.compile(r"(?<!\d)(\d[\d,]*(?:\.\d+)?)\s*(만\s*원|천\s*원|원)")
MONEY_FIELDS = {
    "available_cash": ("쓸 수 있는 돈", "가용 현금", "여유 자금", "보유 현금", "남은 돈"),
    "upcoming_fixed_expense": ("월세", "고정비", "고정 지출", "고정지출", "필수 지출"),
    "upcoming_income": ("예정 수입", "다음 달 수입", "수입", "월급", "급여"),
    "budget": ("여행 예산", "예산"),
}


def extract_money_facts(question: str) -> dict[str, int]:
    """Normalize explicitly labeled monetary facts without inferring missing values."""

    facts: dict[str, int] = {}
    for amount in MONEY_AMOUNT.finditer(question):
        clause_start = max(question.rfind(mark, 0, amount.start()) for mark in (".", "?", "!", "\n")) + 1
        context = question[clause_start:amount.start()]
        matches = (
            (context.rfind(label), field)
            for field, labels in MONEY_FIELDS.items() for label in labels
            if context.rfind(label) >= 0
        )
        nearest = max(matches, default=None, key=lambda item: item[0])
        if nearest is None:
            continue
        number = Decimal(amount[1].replace(",", ""))
        multiplier = 10000 if "만" in amount[2] else 1000 if "천" in amount[2] else 1
        value = number * multiplier
        if value >= 0 and value == value.to_integral_value():
            facts[nearest[1]] = int(value)
    return facts


def _new_state() -> dict[str, Any]:
    return {**{field: {} for field in STATE_FIELDS}, "judgment_facts": {}, "jev_calls_total": 0}


def _allowed_value(key: str, value: Any) -> Any:
    expected = FIELD_TYPES.get(key)
    if expected is None:
        return None
    if isinstance(expected, set):
        if not isinstance(value, list):
            return None
        return sorted({item for item in value if isinstance(item, str) and item in expected})
    if expected is bool:
        return value if isinstance(value, bool) else None
    if expected is int:
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
    if isinstance(value, bool) or not isinstance(value, expected) or value < 0 or not math.isfinite(value):
        return None
    return value


def _minimum_input(state: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Only allowlisted numeric, boolean, and category values can leave the process."""

    scoped = {}
    for key in keys:
        if key in state["judgment_facts"]:
            value = _allowed_value(key, state["judgment_facts"][key])
            if value is not None:
                scoped[key] = value
    return scoped


def _fingerprint(scoped: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(scoped, sort_keys=True).encode()).hexdigest()


def _has_evidence(name: str, scoped: dict[str, Any]) -> bool:
    if name in {"cashflow_harmed", "purchase_burden_score"}:
        return "purchase_price" in scoped and bool(set(scoped) & {"available_cash", "budget", "upcoming_fixed_expense", "upcoming_income"})
    if name == "purchase_choice":
        return "purchase_price" in scoped and bool(set(scoped) & {"available_cash", "current_product_functional", "reported_problems"})
    if name == "upgrade_value_score":
        return bool(set(scoped) & {"requested_upgrade_features", "reported_problems"})
    if name == "key_factor":
        return len(scoped) >= 2
    return bool(scoped)


def _question(name: str) -> Any:
    kind, _, instruction = JUDGMENTS[name]
    instruction += f" Use only state.inputs.{name}. If insufficient, return unknown/low confidence; do not infer missing amounts."
    if kind == "noul":
        return Noul(instructions=instruction)
    if kind == "score":
        return Score(instructions=instruction, criteria=["unknown", "low", "moderate", "high"])
    if kind == "choice":
        return Choice(instructions=instruction, criteria={
            "buy_now": None, "wait": None, "buy_cheaper_variant": None, "unknown": None,
        })
    return Choice(instructions=instruction, criteria={
        "price": None, "replacement_need": None, "feature_gain": None, "cashflow": None, "unknown": None,
    })


def _judge(inputs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """One Jev request containing independent minimal inputs per judgment."""

    _load_key()
    client = TypeSafeClient(model="jev-latest")
    try:
        response = client.system_one(
            state={"inputs": inputs}, questions={name: _question(name) for name in inputs},
        )
        results = {}
        for name in inputs:
            kind = JUDGMENTS[name][0]
            answer = response.nouls[name] if kind == "noul" else response.scores[name] if kind == "score" else response.choices[name]
            value = answer.noul if kind == "noul" else answer.score if kind == "score" else answer.choice
            confidence = abs(float(value) - 0.5) * 2 if kind == "noul" else float(answer.confidence)
            results[name] = {"value": value, "confidence": confidence}
        return results
    except JevError:
        raise
    except Exception as error:
        raise JevError("Jev decision bundle failed.") from error
    finally:
        client.close()


def _compose(results: dict[str, dict[str, Any]], facts: dict[str, Any]) -> dict[str, Any]:
    values = {name: item["value"] for name, item in results.items()}
    action = values.get("purchase_choice", "unknown")
    if isinstance(values.get("cashflow_harmed"), (int, float)) and values["cashflow_harmed"] >= 0.7:
        action = "wait"
    elif (isinstance(values.get("replacement_needed"), (int, float)) and values["replacement_needed"] <= 0.3
          and isinstance(values.get("waiting_low_loss"), (int, float)) and values["waiting_low_loss"] >= 0.7):
        action = "wait"
    composed: dict[str, Any] = {"action": action, "key_factor": values.get("key_factor", "unknown")}
    cash = facts.get("available_cash")
    fixed = facts.get("upcoming_fixed_expense")
    if cash is not None and fixed is not None:
        income = facts.get("upcoming_income", 0)
        composed["cashflow_after_fixed_expenses"] = str(
            Decimal(str(cash)) + Decimal(str(income)) - Decimal(str(fixed))
        )
    return composed


def update_state(path: Path, delta: DecisionDelta) -> dict[str, Any]:
    """Read prior state and evaluate only changed judgments without writes."""

    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else _new_state()
    changed = []
    for field in STATE_FIELDS:
        if field == "jev_results":
            continue
        for key, value in getattr(delta, field).items():
            if state[field].get(key) != value:
                state[field][key] = value
                changed.append(f"{field}.{key}")
    for key, value in delta.judgment_facts.model_dump(exclude_none=True).items():
        sanitized = _allowed_value(key, value)
        if sanitized is not None and state["judgment_facts"].get(key) != sanitized:
            state["judgment_facts"][key] = sanitized
            changed.append(f"judgment_facts.{key}")
    pending: dict[str, dict[str, Any]] = {}
    previously_evaluated = [name for name, item in state["jev_results"].items() if item.get("evaluated")]
    for name, (_, keys, _) in JUDGMENTS.items():
        scoped = _minimum_input(state, keys)
        if state["jev_results"].get(name, {}).get("fingerprint") != _fingerprint(scoped):
            if _has_evidence(name, scoped):
                pending[name] = scoped
            else:
                state["jev_results"][name] = {"value": "unknown", "confidence": 0.0, "evaluated": False, "fingerprint": _fingerprint(scoped)}
    started = time.perf_counter()
    if pending:
        judgments = _judge(pending)
        for name, scoped in pending.items():
            state["jev_results"][name] = {**judgments[name], "evaluated": True, "fingerprint": _fingerprint(scoped)}
        state["jev_calls_total"] += 1
    state["composition"] = _compose(state["jev_results"], state["judgment_facts"])
    state["last_update"] = {
        "changed_keys": changed,
        "jev_calls": 1 if pending else 0,
        "new_judgments": list(pending),
        "reused_judgments": [name for name in previously_evaluated if name not in pending],
        "jev_latency_ms": round((time.perf_counter() - started) * 1000) if pending else 0,
        "transmitted_fields": {name: list(values) for name, values in pending.items()},
    }
    return {"composition": state["composition"], "jev_results": {
        name: {"value": item["value"], "confidence": item["confidence"], "evaluated": item["evaluated"]}
        for name, item in state["jev_results"].items()
    }, "update": state["last_update"]}


def persist_decision_result(path: Path, delta: DecisionDelta, evaluated: dict[str, Any]) -> dict[str, Any]:
    """FastAPI-only state commit after the read-only tool returns."""

    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else _new_state()
    for field in STATE_FIELDS:
        if field != "jev_results":
            state[field].update(getattr(delta, field))
    for key, value in delta.judgment_facts.model_dump(exclude_none=True).items():
        sanitized = _allowed_value(key, value)
        if sanitized is not None:
            state["judgment_facts"][key] = sanitized
    for name, result in evaluated.get("jev_results", {}).items():
        if name not in JUDGMENTS:
            continue
        scoped = _minimum_input(state, JUDGMENTS[name][1])
        state["jev_results"][name] = {
            "value": result["value"], "confidence": result["confidence"],
            "evaluated": result.get("evaluated", False),
            "fingerprint": _fingerprint(scoped),
        }
    state["jev_calls_total"] += evaluated.get("update", {}).get("jev_calls", 0)
    state["composition"] = _compose(state["jev_results"], state["judgment_facts"])
    state["last_update"] = evaluated.get("update", {})
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)
    return state
