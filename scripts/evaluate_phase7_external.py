"""Run one separately reported billable Phase 7 Web Search and MCP check."""

import asyncio
import json
import time

from spendguard.agent import OpenAIAnalyzer
from spendguard.decision_packs import build_decision_pack


QUESTION = "Apple iPhone current Korea sale price from official source"
DATA = {
    "target": "iPhone",
    "purpose": "purchase comparison",
    "price": "user will confirm current price",
    "options": [
        {"name": "official", "total_cost": "100"},
        {"name": "alternative", "total_cost": "110"},
    ],
}


async def main() -> None:
    started_at = time.perf_counter()
    analysis = await OpenAIAnalyzer().analyze(QUESTION)
    agent_latency_ms = (time.perf_counter() - started_at) * 1_000
    decision_started_at = time.perf_counter()
    decision = await build_decision_pack(analysis, DATA)
    decision_latency_ms = (time.perf_counter() - decision_started_at) * 1_000
    print(
        json.dumps(
            {
                "research": analysis.research.model_dump(),
                "decision": {"pack": decision.pack, "status": decision.status},
                "source_traces": [
                    {
                        "source_name": fact.source_name,
                        "source_url": fact.source_url,
                        "retrieved_at": fact.retrieved_at,
                    }
                    for fact in decision.sources
                ],
                "latency_ms": {
                    "openai_agent_with_web_search": agent_latency_ms,
                    "decision_pack_with_mcp": decision_latency_ms,
                    "total": agent_latency_ms + decision_latency_ms,
                },
                "calls": {
                    "jev": 0,
                    "openai_agent": 1,
                    "web_search_tool_call_count": "not exposed by AnalysisResult",
                    "web_search_query_count": len(analysis.research.queries),
                    "mcp": len(decision.calculations),
                },
                "usage": "not exposed by the current Agent SDK result boundary",
                "cost": "not calculated because usage is unavailable at this boundary",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
