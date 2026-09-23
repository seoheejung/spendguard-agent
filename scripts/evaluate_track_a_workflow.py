"""Compare the unchanged production path with a Jev-observed experimental path."""

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from agents import Runner

from spendguard.agent import OpenAIAnalyzer, load_project_env, needs_current_information
from spendguard.decision_packs import build_decision_pack
from spendguard.decision_prototype import append_sanitized_log, build_prototype_client, fixture_sha256, judge


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evals" / "track_a_workflow_cases.json"
LOG = ROOT / "docs" / "results" / "track-a-jev-decisions.jsonl"
REPORT = ROOT / "docs" / "results" / "track-a-workflow-evaluation.json"


def _runner_observer(counters: dict[str, dict[str, int]]) -> None:
    original = Runner.run

    async def tracked(*args, **kwargs):
        name = "active"
        counters[name]["calls"] += 1
        started = time.perf_counter()
        result = await original(*args, **kwargs)
        counters[name]["latency_ms"] += (time.perf_counter() - started) * 1_000
        for response in getattr(result, "raw_responses", []):
            usage = getattr(response, "usage", None)
            if usage is not None:
                counters[name]["input_tokens"] += getattr(usage, "input_tokens", 0) or 0
                counters[name]["output_tokens"] += getattr(usage, "output_tokens", 0) or 0
                details = getattr(usage, "input_tokens_details", None)
                counters[name]["cached_input_tokens"] += getattr(details, "cached_tokens", 0) or 0
            counters[name]["web_search_calls"] += sum(
                getattr(item, "type", None) == "web_search_call"
                for item in getattr(response, "output", [])
            )
        return result

    Runner.run = staticmethod(tracked)


async def main() -> None:
    load_project_env()
    dataset = json.loads(FIXTURE.read_text(encoding="utf-8"))
    jev = build_prototype_client()
    analyzer = OpenAIAnalyzer()
    counters = {"active":{"calls":0,"latency_ms":0,"input_tokens":0,"cached_input_tokens":0,"output_tokens":0,"web_search_calls":0}}
    outcomes = []
    grouped = {"baseline":[],"experimental":[]}
    jev_usage = {"calls":0,"input_tokens":0,"output_tokens":0,"latency_ms":0.0,"cost_usd":0.0}
    original_runner = Runner.run
    total_started = time.perf_counter()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        _runner_observer(counters)
        for case in dataset["cases"]:
            common_state = {"request":case["question"],"provided_fields":case["data"]}

            counters["active"] = {"calls":0,"latency_ms":0,"input_tokens":0,"cached_input_tokens":0,"output_tokens":0,"web_search_calls":0}
            started = time.perf_counter()
            base_analysis = await analyzer.analyze(case["question"])
            base_decision = await build_decision_pack(base_analysis, case["data"])
            baseline = {**counters["active"],"end_to_end_latency_ms":(time.perf_counter()-started)*1_000,
                        "intent":base_analysis.intent,"status":base_decision.status,
                        "source_count":len(base_analysis.external_facts),
                        "unsupported_fact_count":sum(not (x.value and x.source_name and x.source_url and x.retrieved_at) for x in base_analysis.external_facts)}
            grouped["baseline"].append(baseline)

            counters["active"] = {"calls":0,"latency_ms":0,"input_tokens":0,"cached_input_tokens":0,"output_tokens":0,"web_search_calls":0}
            started = time.perf_counter()
            info_result = judge("additional_information", common_state, client=jev)
            search_result = judge("current_information_search", common_state, client=jev)
            experimental_analysis = await analyzer.analyze(case["question"])
            relevant = []
            included_facts = []
            for fact in experimental_analysis.external_facts:
                candidate = {"query":case["question"],"result":{"title":fact.source_name,"snippet":fact.value,"url":fact.source_url}}
                relevance = judge("search_result_relevance",candidate,client=jev)
                relevant.append(relevance)
                if relevance.typed_result != "not_relevant":
                    included_facts.append(fact)
            experimental_analysis = experimental_analysis.model_copy(update={"external_facts":included_facts})
            decision = await build_decision_pack(experimental_analysis, case["data"])
            review_state = {"result":{"conclusion":decision.conclusion,"facts":decision.facts,"risks":decision.risks},
                            "evidence":{"sources":[fact.model_dump(mode="json") for fact in decision.sources],"calculations":[item.model_dump(mode="json") for item in decision.calculations]}}
            review_result = judge("decision_result_review",review_state,client=jev)
            jev_results = [info_result, search_result, *relevant, review_result]
            for item in jev_results:
                jev_usage["calls"] += 1
                jev_usage["input_tokens"] += item.input_tokens or 0
                jev_usage["output_tokens"] += item.output_tokens or 0
                jev_usage["latency_ms"] += item.latency_ms
                jev_usage["cost_usd"] += item.estimated_cost_usd or 0.0
            review_question = (
                "Review the experimental Jev judgments and the existing decision result. "
                "Check for unsupported claims, missing decision-critical information, search need, "
                "and evidence gaps. Do not take actions. State any issue requiring user attention.\n"
                + json.dumps({"jev":{"additional_information":info_result.typed_result,
                                    "current_information_search":search_result.typed_result,
                                    "search_result_relevance":[result.typed_result for result in relevant],
                                    "decision_result_review":review_result.typed_result},**review_state},ensure_ascii=False)
            )
            await analyzer.analyze(review_question)
            review_agent_called = True
            experimental = {**counters["active"],"end_to_end_latency_ms":(time.perf_counter()-started)*1_000,
                            "intent":experimental_analysis.intent,"status":decision.status,
                            "source_count":len(experimental_analysis.external_facts),
                            "unsupported_fact_count":sum(not (x.value and x.source_name and x.source_url and x.retrieved_at) for x in experimental_analysis.external_facts),
                            "jev":{"additional_information":info_result.typed_result,"current_information_search":search_result.typed_result,
                                   "search_result_relevance":[result.typed_result for result in relevant],"decision_result_review":review_result.typed_result,
                                   "review_agent_called":review_agent_called,
                                   "usage":{"calls":len(jev_results),"input_tokens":sum(item.input_tokens or 0 for item in jev_results),
                                            "output_tokens":sum(item.output_tokens or 0 for item in jev_results),
                                            "latency_ms":sum(item.latency_ms for item in jev_results),
                                            "cost_usd":sum(item.estimated_cost_usd or 0.0 for item in jev_results)}}}
            grouped["experimental"].append(experimental)
            outcome = {"id":case["id"],"expected_intent":case["expected_intent"],"expected_status":case["expected_status"],
                             "expected_source":case["expected_source"],"baseline":baseline,"experimental":experimental,
                             "baseline_success":baseline["intent"]==case["expected_intent"] and baseline["status"]==case["expected_status"] and (not case["expected_source"] or baseline["source_count"]>0),
                             "experimental_success":experimental["intent"]==case["expected_intent"] and experimental["status"]==case["expected_status"] and (not case["expected_source"] or experimental["source_count"]>0)}
            outcomes.append(outcome)
            event_results = [
                (info_result, None),
                (search_result, "yes" if needs_current_information(case["question"]) else "no"),
                *((result, None) for result in relevant),
                (review_result, None),
            ]
            for event_result, expected in event_results:
                append_sanitized_log(
                    LOG,
                    case_id=f"{run_id}:{case['id']}:{event_result.judgment_id}",
                    result=event_result,
                    expected=expected,
                    workflow_success=outcome["experimental_success"],
                    selected_path=(
                        "code_rule" if event_result.judgment_id == "current_information_search" else
                        "automatic_filter" if event_result.judgment_id == "search_result_relevance" and not event_result.abstained else
                        "openai_agent_review"
                    ),
                )
    finally:
        Runner.run = staticmethod(original_runner)
        jev.close()

    def summarize(rows):
        return {"agent_calls":sum(row["calls"] for row in rows),"agent_latency_ms":sum(row["latency_ms"] for row in rows),
                "end_to_end_latency_ms":sum(row["end_to_end_latency_ms"] for row in rows),
                "input_tokens":sum(row["input_tokens"] for row in rows),"cached_input_tokens":sum(row["cached_input_tokens"] for row in rows),
                "output_tokens":sum(row["output_tokens"] for row in rows),
                "web_search_calls":sum(row["web_search_calls"] for row in rows),
                "source_coverage":sum(row["source_count"]>0 for row,case in zip(rows,dataset["cases"]) if case["expected_source"])/sum(case["expected_source"] for case in dataset["cases"]),
                "unsupported_fact_count":sum(row["unsupported_fact_count"] for row in rows)}
    summary={key:summarize(rows) for key,rows in grouped.items()}
    summary["agent_calls_reduced"] = summary["baseline"]["agent_calls"]-summary["experimental"]["agent_calls"]
    summary["agent_input_tokens_reduced"] = summary["baseline"]["input_tokens"]-summary["experimental"]["input_tokens"]
    summary["jev"] = jev_usage
    summary["end_to_end_success"]={"baseline":sum(row["baseline_success"] for row in outcomes),"experimental":sum(row["experimental_success"] for row in outcomes),"total":len(outcomes)}
    summary["optimized_candidate"] = {
        **summary["baseline"],
        "jev_calls": 0,
        "separately_executed": False,
        "basis": "The selected Code-owned judgments already use this unchanged production path; this candidate is equivalent to baseline.",
    }
    model = os.getenv("OPENAI_MODEL")
    rates = {"gpt-5.6-sol":(4.0,0.4,20.0),"gpt-5.6-terra":(2.0,0.2,12.0),"gpt-5.6-luna":(0.2,0.02,1.2)}
    for key, rows in grouped.items():
        totals=summary[key]
        rate=rates.get(model or "")
        totals["model_cost_usd"] = None if rate is None else ((totals["input_tokens"]-totals["cached_input_tokens"])*rate[0]+totals["cached_input_tokens"]*rate[1]+totals["output_tokens"]*rate[2])/1_000_000
        totals["web_search_cost_usd"] = totals["web_search_calls"]*0.01/1_000
        totals["total_openai_cost_usd"] = None if rate is None else totals["model_cost_usd"]+totals["web_search_cost_usd"]
        totals["model_cost_status"] = "unverified_model_price" if rate is None else "official_public_price"
    report = {"dataset_version":dataset["dataset_version"],"fixture_sha256":fixture_sha256(FIXTURE),"model":model,
              "measured_at":datetime.now(timezone.utc).isoformat(),
              "total_elapsed_ms":(time.perf_counter()-total_started)*1_000,"summary":summary,"outcomes":outcomes,
              "openai_price_source":"https://developers.openai.com/api/docs/models/gpt-5.6-luna",
              "openai_price_checked":"2026-09-23",
              "openai_web_search_price_source":"https://developers.openai.com/api/docs/pricing",
              "openai_cost_note":"Includes model tokens and Web Search calls; any other tools are reported separately.",
              "code_search_decision":"needs_current_information(question) remains the active production decision in both paths."}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    asyncio.run(main())
