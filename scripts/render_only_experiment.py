"""One AirPods A/B experiment with live evidence and a tool-free final renderer."""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
import time
import urllib.request
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

import httpx

from spendguard.codex_runtime import CodexRunner
from spendguard.decision_state import DecisionDelta, extract_money_facts, persist_decision_result, update_state
from spendguard.main import app, lifespan
from spendguard.mcp_client import call_calculation_tool


QUESTION = (
    "지금 쓰는 에어팟은 3년 넘었고 아직 작동하지만 배터리가 빨리 닳아. "
    "에어팟 4 일반 모델과 액티브 노이즈 캔슬링 모델 중 무엇을 살지 고민이야. "
    "다음 달 여행비도 고려해야 해서 현재 가격과 실제 차이, 지금 사는 것과 기다리는 것을 비교해줘."
)
FOLLOW_UP = (
    "현재 쓸 수 있는 돈이 43만원이고 다음 달 월세 60만원과 수입 13만원도 있어. "
    "앞서 확인한 가격을 기준으로 지금 사도 괜찮을까?"
)
APPLE_RELEASE = (
    "https://www.apple.com/kr/newsroom/2024/09/"
    "apple-introduces-all-new-airpods-4-with-industry-defining-audio-and-design/"
)
APPLE_COMPARE = "https://www.apple.com/kr/airpods/compare/"


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hidden = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def public_get(url: str) -> tuple[str, float]:
    started = time.perf_counter()
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SpendGuard/0.1"})
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read(1_000_000).decode("utf-8", errors="replace")
    return body, time.perf_counter() - started


def collect_evidence() -> tuple[list[dict[str, str]], dict[str, int | str | float]]:
    article, release_seconds = public_get(APPLE_RELEASE)
    comparison, compare_seconds = public_get(APPLE_COMPARE)
    if "AirPods 4" not in comparison:
        raise RuntimeError("The official comparison page did not mention AirPods 4.")
    parser = VisibleText()
    parser.feed(article)
    text = re.sub(r"\s+", " ", " ".join(parser.parts).replace("\xa0", " "))
    marker = text.find("가격 및 출시 일정")
    if marker < 0:
        raise RuntimeError("Official price section not found.")
    section = text[marker:marker + 1800]
    prices = {}
    for name, pattern in {
        "AirPods 4": r"AirPods 4는.{0,220}?(\d[\d,]+)원",
        "AirPods 4 ANC": r"AirPods 4 액티브 노이즈 캔슬링 모델은.{0,220}?(\d[\d,]+)원",
    }.items():
        match = re.search(pattern, section)
        if not match:
            raise RuntimeError(f"Official price not found for {name}.")
        prices[name] = int(match[1].replace(",", ""))
    return (
        [{"title": "Apple AirPods 4 launch announcement (2024-09-09)", "url": APPLE_RELEASE},
         {"title": "Apple AirPods model comparison", "url": APPLE_COMPARE}],
        {**prices, "search_calls": 0, "web_source_fetches": 2,
         "source_fetch_seconds": release_seconds + compare_seconds,
         "price_type": "2024 launch price, not current checkout price"},
    )


async def baseline() -> dict:
    async with lifespan(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://spendguard") as client:
            response = await client.post("/api/decisions", json={"question": QUESTION, "mode": "jev"}, timeout=180)
            response.raise_for_status()
            return response.json()


async def render_only() -> dict:
    started = time.perf_counter()
    sources, search = await asyncio.to_thread(collect_evidence)
    search_done = time.perf_counter()
    prices = {name: search[name] for name in ("AirPods 4", "AirPods 4 ANC")}
    calculation = await call_calculation_tool("compare_costs", {
        "options": [{"name": name, "total_cost": price} for name, price in prices.items()],
        "currency": "KRW",
    })
    calculation_done = time.perf_counter()
    difference = prices["AirPods 4 ANC"] - prices["AirPods 4"]
    if Decimal(str(calculation["result"]["difference_from_AirPods 4 ANC"])) != difference:
        raise RuntimeError("MCP price difference mismatch.")
    with tempfile.TemporaryDirectory(prefix="spendguard-render-state-") as directory:
        state_path = Path(directory) / "state.json"
        first_delta = DecisionDelta(
            user_facts={"age": "3+ years", "functional": True, "battery": "degraded", "travel": "next month"},
            current_facts={"price_type": search["price_type"]},
            alternatives={name: {"price": price} for name, price in prices.items()},
            calculations={"price_difference": difference},
            sources={"Apple launch release": APPLE_RELEASE},
            judgment_facts={
                "current_product_age_months": 36, "current_product_functional": True,
                "reported_problems": ["battery"], "requested_upgrade_features": ["noise_cancellation"],
                "purchase_price": prices["AirPods 4"], "alternative_price": prices["AirPods 4 ANC"],
            },
        )
        decision = await asyncio.to_thread(update_state, state_path, first_delta)
        persist_decision_result(state_path, first_delta, decision)
        jev_done = time.perf_counter()
        bundle = {
            "user_facts": first_delta.user_facts,
            "verified_facts": {"prices_krw": prices, "price_type": search["price_type"],
                               "source": sources[0], "features": {
                                   "standard": "no active noise cancellation, USB-C case",
                                   "ANC": "active noise cancellation and wireless charging case",
                               }},
            "calculated": {"price_difference_krw": difference},
            "decision": {"composition": decision["composition"],
                         "judgments": decision["jev_results"]},
            "answer_scope": "Compare AirPods 4 standard, ANC, and waiting. Travel budget amount is unknown.",
        }
        runner = CodexRunner()
        first = await runner.render(bundle)
        first_done = time.perf_counter()
        follow_facts = extract_money_facts(FOLLOW_UP)
        follow_delta = DecisionDelta(judgment_facts=follow_facts)
        follow_decision = await asyncio.to_thread(update_state, state_path, follow_delta)
        persist_decision_result(state_path, follow_delta, follow_decision)
        follow_jev_done = time.perf_counter()
        follow_bundle = {
            "user_facts": {**first_delta.user_facts, **follow_facts},
            "verified_facts": {"prices_krw": prices, "price_type": search["price_type"], "source": sources[0]},
            "calculated": {"price_difference_krw": difference,
                           "cashflow_after_fixed_expenses_krw": follow_decision["composition"].get("cashflow_after_fixed_expenses")},
            "decision": {"composition": follow_decision["composition"],
                         "updated_judgments": {name: follow_decision["jev_results"][name]
                                               for name in follow_decision["update"]["new_judgments"]},
                         "reused_judgments": follow_decision["update"]["reused_judgments"]},
            "answer_scope": "Only answer whether buying now fits the updated cashflow. Reuse the prior prices.",
        }
        follow = await runner.render(follow_bundle)
        follow_done = time.perf_counter()
        return {
            "first": {"total_ms": round((first_done - started) * 1000),
                      "search_ms": round((search_done - started) * 1000),
                      "mcp_ms": round((calculation_done - search_done) * 1000),
                      "jev_ms": round((jev_done - calculation_done) * 1000),
                      "codex_ms": first.latency_ms, "first_visible_event_ms": first.first_visible_event_ms,
                      "search_calls": search["search_calls"],
                      "web_source_fetches": search["web_source_fetches"], "mcp_calls": 1,
                      "jev_requests": decision["update"]["jev_calls"],
                      "jev_judgments": len(decision["update"]["new_judgments"]),
                      "model_turns": first.model_turns, "answer": first.answer,
                      "suggested_followups": first.suggested_followups},
            "followup": {"total_ms": round((follow_done - first_done) * 1000),
                         "jev_ms": round((follow_jev_done - first_done) * 1000),
                         "codex_ms": follow.latency_ms,
                         "first_visible_event_ms": follow.first_visible_event_ms,
                         "search_calls": 0, "mcp_calls": 0,
                         "jev_requests": follow_decision["update"]["jev_calls"],
                         "jev_judgments": len(follow_decision["update"]["new_judgments"]),
                         "reused_judgments": len(follow_decision["update"]["reused_judgments"]),
                         "model_turns": follow.model_turns, "answer": follow.answer,
                         "suggested_followups": follow.suggested_followups},
            "sources": sources,
        }


async def main() -> None:
    import sys

    if "--probe-search" in sys.argv:
        sources, search = await asyncio.to_thread(collect_evidence)
        print(json.dumps({"sources": sources, "search": search}, ensure_ascii=True))
        return
    result = {"render_only": await render_only()}
    if "--with-baseline" in sys.argv:
        result["baseline"] = await baseline()
    path = Path("docs/results/chapter-b-render-only-observation.json")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"baseline": result.get("baseline", {}).get("metadata"),
                      "render_only": {turn: {key: value for key, value in details.items()
                                              if key not in {"answer", "suggested_followups"}}
                                      for turn, details in result["render_only"].items()
                                      if turn in {"first", "followup"}}}, ensure_ascii=True))


if __name__ == "__main__":
    asyncio.run(main())
