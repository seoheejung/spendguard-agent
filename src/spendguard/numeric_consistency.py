"""Deterministic checks for monetary claims in a final answer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MONEY = re.compile(r"(?<![\d,])(?P<sign>[-−]?)(?P<amount>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<fraction>\d{1,2}))?\s*원")
DIFFERENCE = re.compile(r"차액|차이|절감|절약|저렴|비싸|할인액|더\s+(?:싸|비싸)")
COMPARISON = re.compile(r"차액|차이|절감|절약|저렴|비싸|낮|높")
PRICE_ROLES = {
    "public": re.compile(r"공개가|표시가|정가|정상가|시중가"),
    "paid": re.compile(r"예약가|예약\s*(?:가격|내역)|결제가|구매가|지불액"),
    "coupon": re.compile(r"쿠폰\s*(?:적용\s*(?:가|시)|가)|할인가"),
}
TOTAL = re.compile(r"총액|합계")
REMAINING = re.compile(r"잔액|남은\s*(?:돈|예산)|예산\s*잔여")
MONTHLY = re.compile(r"월간|월\s*(?:비용|금액|지출)")
ANNUAL = re.compile(r"연간|연\s*(?:비용|금액|지출)")


@dataclass(frozen=True)
class Amount:
    start: int
    end: int
    value: Decimal


def _amounts(text: str, offset: int = 0) -> list[Amount]:
    found = []
    for match in MONEY.finditer(text):
        value = Decimal(match["amount"].replace(",", ""))
        if match["fraction"]:
            value += Decimal("0." + match["fraction"])
        if match["sign"]:
            value = -value
        found.append(Amount(offset + match.start(), offset + match.end(), value))
    return found


def _format(value: Decimal) -> str:
    if value == value.to_integral_value():
        return f"{value:,.0f}원"
    return f"{value:,.2f}원"


def _derived_amounts(calls: list[dict]) -> dict[str, set[Decimal]]:
    """Use completed calculation outputs, including comparison differences."""

    values: dict[str, set[Decimal]] = {"difference": set(), "total": set(), "remaining": set(), "annual": set(), "monthly": set()}
    for call in calls:
        if call.get("status") != "completed" or call.get("tool") == "update_decision_state":
            continue
        result = (call.get("result") or {}).get("result") or {}
        for key, raw in result.items():
            try:
                amount = Decimal(str(raw))
            except (ValueError, ArithmeticError):
                continue
            if key.startswith("difference_from_") and amount != 0:
                values["difference"].add(abs(amount))
            elif key in {"savings", "total_interest"}:
                values["difference"].add(abs(amount))
            elif key in {"total_cost", "total_payment", "new_remaining_total", "tco"}:
                values["total"].add(amount)
            elif key == "budget_remaining":
                values["remaining"].add(amount)
            elif key == "annual_amount":
                values["annual"].add(amount)
            elif key == "monthly_payment":
                values["monthly"].add(amount)
    return values


def _table_claims(answer: str) -> list[tuple[Amount, Decimal]]:
    claims = []
    header: list[str] | None = None
    offset = 0
    for line in answer.splitlines(keepends=True):
        if not line.lstrip().startswith("|"):
            header = None
            offset += len(line)
            continue
        cells = line.split("|")
        if len(cells) < 4:
            offset += len(line)
            continue
        inner = cells[1:-1]
        if all(re.fullmatch(r"\s*:?-{3,}:?\s*", cell) for cell in inner):
            offset += len(line)
            continue
        if header is None:
            header = [cell.strip() for cell in inner]
            offset += len(line)
            continue
        if len(inner) != len(header):
            offset += len(line)
            continue
        cursor = offset + 1
        amounts: list[Amount | None] = []
        for cell in inner:
            tokens = _amounts(cell, cursor)
            amounts.append(tokens[0] if len(tokens) == 1 else None)
            cursor += len(cell) + 1
        for index, label in enumerate(header):
            target = amounts[index]
            if target is None:
                continue
            prior = [amount for amount in amounts[:index] if amount is not None]
            if DIFFERENCE.search(label) and len(prior) >= 2:
                claims.append((target, abs(prior[-2].value - prior[-1].value)))
            elif TOTAL.search(label) and len(prior) >= 2:
                claims.append((target, sum((amount.value for amount in prior), Decimal(0))))
            elif REMAINING.search(label) and len(prior) >= 2:
                claims.append((target, prior[-2].value - prior[-1].value))
            elif ANNUAL.search(label) and len(prior) >= 1 and any(MONTHLY.search(item) for item in header[:index]):
                claims.append((target, prior[-1].value * 12))
        offset += len(line)
    return claims


def _prose_claims(answer: str, derived: dict[str, set[Decimal]]) -> list[tuple[Amount, Decimal]]:
    claims = []
    offset = 0
    for line in answer.splitlines(keepends=True):
        if line.lstrip().startswith("|"):
            offset += len(line)
            continue
        segment_start = 0
        for boundary in re.finditer(r"[.!?](?:\s|$)", line):
            segment = line[segment_start:boundary.end()]
            claims.extend(_segment_claims(segment, offset + segment_start, derived))
            segment_start = boundary.end()
        claims.extend(_segment_claims(line[segment_start:], offset + segment_start, derived))
        offset += len(line)
    return claims


def _segment_claims(segment: str, offset: int, derived: dict[str, set[Decimal]]) -> list[tuple[Amount, Decimal]]:
    amounts = _amounts(segment, offset)
    if not amounts:
        return []
    if DIFFERENCE.search(segment):
        if len(amounts) == 3 and DIFFERENCE.search(segment[amounts[-2].end - offset:]):
            return [(amounts[-1], abs(amounts[-3].value - amounts[-2].value))]
        if len(amounts) == 1 and len(derived["difference"]) == 1:
            return [(amounts[0], next(iter(derived["difference"])))]
    if len(amounts) == 2 and re.search(r"\d+(?:\.\d+)?\s*%", segment) and re.search(r"쿠폰|할인", segment):
        percent = re.search(r"(\d+(?:\.\d+)?)\s*%", segment)
        assert percent is not None
        expected = (amounts[0].value * (Decimal(1) - Decimal(percent[1]) / 100)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        return [(amounts[1], expected)]
    for marker, key in ((TOTAL, "total"), (REMAINING, "remaining"), (ANNUAL, "annual"), (MONTHLY, "monthly")):
        if len(derived[key]) != 1:
            continue
        if len(amounts) == 1 and marker.search(segment):
            return [(amounts[0], next(iter(derived[key])))]
        if len(amounts) >= 2 and marker.search(segment[amounts[-2].end - offset:amounts[-1].start - offset]):
            return [(amounts[-1], next(iter(derived[key])))]
    return []


def _price_role_claims(answer: str) -> list[tuple[Amount, Decimal]]:
    """Cross-check a comparison against uniquely labeled prices in the same answer."""

    role_values: dict[str, set[Decimal]] = {name: set() for name in PRICE_ROLES}
    for line in answer.splitlines(keepends=True):
        if not line.lstrip().startswith("|") and COMPARISON.search(line):
            continue
        for token in _amounts(line):
            before = line[max(0, token.start - 65):token.start]
            matches = [
                (match.end(), role) for role, pattern in PRICE_ROLES.items()
                for match in pattern.finditer(before)
            ]
            if matches:
                role_values[max(matches)[1]].add(token.value)
    unique = {role: next(iter(values)) for role, values in role_values.items() if len(values) == 1}
    claims = []
    offset = 0
    for line in answer.splitlines(keepends=True):
        if line.lstrip().startswith("|"):
            offset += len(line)
            continue
        for token in _amounts(line):
            if token.value in unique.values():
                continue
            before = line[max(0, token.start - 75):token.start]
            after = line[token.end:min(len(line), token.end + 18)]
            context = before + after
            if not COMPARISON.search(context):
                continue
            if "public" in unique and "paid" in unique and PRICE_ROLES["public"].search(before) and PRICE_ROLES["paid"].search(before):
                claims.append((Amount(offset + token.start, offset + token.end, token.value), abs(unique["public"] - unique["paid"])))
            elif "coupon" in unique and "paid" in unique and PRICE_ROLES["coupon"].search(before) and PRICE_ROLES["paid"].search(before):
                claims.append((Amount(offset + token.start, offset + token.end, token.value), abs(unique["coupon"] - unique["paid"])))
        offset += len(line)
    return claims


def correct_numeric_answer(answer: str, calls: list[dict]) -> tuple[str, int]:
    """Correct unambiguous derived amounts without another model call."""

    derived = _derived_amounts(calls)
    claims = _table_claims(answer) + _prose_claims(answer, derived) + _price_role_claims(answer)
    corrections = [(target, expected) for target, expected in claims if target.value != expected]
    if not corrections:
        return answer, 0
    explicit: dict[tuple[int, int], Decimal] = {}
    for target, expected in corrections:
        key = (target.start, target.end)
        if key in explicit and explicit[key] != expected:
            raise ValueError("Conflicting monetary corrections")
        explicit[key] = expected
    patches = []
    for token in _amounts(answer):
        expected = explicit.get((token.start, token.end))
        if expected is not None:
            patches.append((token.start, token.end, _format(expected)))
    for start, end, replacement in reversed(patches):
        answer = answer[:start] + replacement + answer[end:]
    return answer, len(patches)
