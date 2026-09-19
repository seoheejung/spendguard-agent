"""OpenAI analysis and current-information research for SpendGuard."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agents import Agent, ModelSettings, Runner, WebSearchTool

from spendguard.models import AgentResearchOutput, AnalysisResult, ExternalFact, ResearchResult


class AgentConfigurationError(RuntimeError):
    """Missing required OpenAI configuration."""


class AgentExecutionError(RuntimeError):
    """OpenAI agent run failed."""


class ResearchExecutionError(AgentExecutionError):
    """OpenAI web search could not be completed."""


INSTRUCTIONS = """
You are SpendGuard's intake and current-information research agent. Analyze one
Korean or English consumer spending question. Return only the required structured output.

Classify intent as exactly one of:
- purchase: buying a product, used product, replacement, or purchase timing
- recurring_cost: subscription, communication bill, or other recurring expense
- finance_cost: loan, interest, refinancing, or finance cost question
- ownership_cost: vehicle or other asset ownership expense
- quote_audit: quote, estimate, or contract-cost review
- budget_optimization: household budget, spending reduction, or budget planning
- unknown: ambiguous, unrelated, or outside those categories

Keep user-provided facts in known_facts. Do not calculate, use MCP, make a purchase
decision, or invent facts, prices, policies, specifications, sources, or dates.
List information absent from the request in missing_fields and keep interpretive
assumptions separate in assumptions.

When WebSearchTool is available, it is required for this request. Build precise
queries from the user's product/service, market, and requested current fact. Prefer
official manufacturer, service, institution, or official sales/policy pages. Only
put a search-derived value in external_facts when the value is supported by a cited
URL. Give each item a source_url from a cited result. Do not create retrieved_at,
source_name, published_at, or a URL. Put no external fact in the user facts or in
the explanation. If no source supports a value, leave external_facts empty. Mark
official_source_urls only with cited official URLs. Set conflicting_sources when
credible cited sources materially disagree; do not resolve the conflict yourself.
Set freshness_confirmed only when the cited source itself supports that the value is
current; otherwise leave it false and do not present the value as confirmed.
""".strip()


CURRENT_INFORMATION_TERMS = re.compile(
    r"(?:current|latest|today|now|price|pricing|plan(?:s)?|subscription|policy|promotion|"
    r"spec(?:ification)?s?|sale(?:s)?\s+terms|available|현재|최신|오늘|지금|가격|요금제?|구독|"
    r"정책|프로모션|사양|판매\s*조건|할인|특가)",
    re.IGNORECASE,
)
CALCULATION_ONLY_TERMS = re.compile(
    r"(?:calculate|calculation|total|installment|interest|formula|계산|합계|할부|이자|공식)",
    re.IGNORECASE,
)
USER_PROVIDED_AMOUNT = re.compile(r"\d[\d,]*(?:\s*(?:원|만원|달러|usd|krw|%))", re.IGNORECASE)


def needs_current_information(question: str) -> bool:
    """Return true only for the Phase 5 categories of mutable external facts."""

    if not CURRENT_INFORMATION_TERMS.search(question):
        return False
    return not (
        CALCULATION_ONLY_TERMS.search(question)
        and USER_PROVIDED_AMOUNT.search(question)
        and not re.search(r"(?:현재|최신|today|latest|now)", question, re.IGNORECASE)
    )


def load_project_env(env_path: Path | None = None) -> None:
    """Load unset environment variables from the project .env file."""

    path = env_path or Path(__file__).resolve().parents[2] / ".env"
    if not path.is_file():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def build_agent(*, research_enabled: bool = False) -> Agent:
    """Create the agent, enabling hosted web search only when required."""

    load_project_env()
    model = os.getenv("OPENAI_MODEL")
    if not model:
        raise AgentConfigurationError("OPENAI_MODEL is required.")
    if not os.getenv("OPENAI_API_KEY"):
        raise AgentConfigurationError("OPENAI_API_KEY is required.")

    model_settings = ModelSettings()
    tools = []
    if research_enabled:
        tools = [WebSearchTool(search_context_size="medium", external_web_access=True)]
        model_settings = ModelSettings(
            tool_choice="required",
            response_include=["web_search_call.action.sources"],
        )

    return Agent(
        name="SpendGuard Core Agent",
        instructions=INSTRUCTIONS,
        model=model,
        model_settings=model_settings,
        tools=tools,
        output_type=AgentResearchOutput if research_enabled else AnalysisResult,
    )


def _item_value(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _normalize_url(url: str) -> str:
    return url.rstrip("/")


def _host_name(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.") or url


def _extract_cited_sources(run_result: Any) -> tuple[dict[str, str], list[str], bool]:
    """Collect only URLs emitted by the actual Responses web-search output."""

    sources: dict[str, str] = {}
    queries: list[str] = []
    web_search_called = False
    for response in getattr(run_result, "raw_responses", []):
        for item in _item_value(response, "output", []):
            item_type = _item_value(item, "type")
            if item_type == "web_search_call":
                web_search_called = True
                action = _item_value(item, "action", {})
                action_type = _item_value(action, "type")
                if action_type == "search":
                    queries.extend(_item_value(action, "queries", []) or [])
                    query = _item_value(action, "query")
                    if query:
                        queries.append(query)
                    for source in _item_value(action, "sources", []) or []:
                        url = _item_value(source, "url")
                        if url:
                            sources.setdefault(_normalize_url(url), _host_name(url))
            if item_type == "message":
                for content in _item_value(item, "content", []) or []:
                    for annotation in _item_value(content, "annotations", []) or []:
                        if _item_value(annotation, "type") != "url_citation":
                            continue
                        url = _item_value(annotation, "url")
                        if url:
                            sources[_normalize_url(url)] = _item_value(annotation, "title") or _host_name(url)
    return sources, list(dict.fromkeys(queries)), web_search_called


def _normalize_research(run_result: Any, output: AgentResearchOutput) -> AnalysisResult:
    """Attach timestamps and accept facts only when their source URL was actually cited."""

    sources, queries, web_search_called = _extract_cited_sources(run_result)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    external_facts: list[ExternalFact] = []
    for fact in output.external_facts:
        value = fact.value.strip()
        source_url = fact.source_url.strip()
        normalized_url = _normalize_url(source_url)
        if not value or normalized_url not in sources:
            continue
        external_facts.append(
            ExternalFact(
                value=value,
                source_name=sources[normalized_url],
                source_url=source_url,
                retrieved_at=retrieved_at,
            )
        )

    official_urls = {_normalize_url(url) for url in output.official_source_urls}
    official_source_confirmed = bool(official_urls & set(sources))
    if not web_search_called or not sources:
        status = "no_results"
        note = "Web Search returned no citable current-information source."
    elif output.conflicting_sources:
        status = "conflicting"
        note = "Cited sources conflict; no single current value was confirmed."
    elif not output.freshness_confirmed:
        status = "freshness_unverifiable"
        note = "The source does not let us confirm that the value is current."
    elif not official_source_confirmed:
        status = "official_source_unconfirmed"
        note = "Citable sources were found, but an official source was not confirmed."
    else:
        status = "completed"
        note = "Current external facts are listed separately with their sources."

    if status in {"conflicting", "freshness_unverifiable"}:
        external_facts = []

    return AnalysisResult(
        intent=output.intent,
        summary=output.summary,
        known_facts=output.known_facts,
        missing_fields=output.missing_fields,
        assumptions=output.assumptions,
        research=ResearchResult(
            needed=True,
            status=status,
            queries=queries,
            official_source_confirmed=official_source_confirmed,
            note=note,
        ),
        external_facts=external_facts,
    )


class OpenAIAnalyzer:
    """Adapter that runs the configured OpenAI Agent SDK agent."""

    async def analyze(self, question: str) -> AnalysisResult:
        research_enabled = needs_current_information(question)
        try:
            result = await Runner.run(build_agent(research_enabled=research_enabled), question)
            if not research_enabled:
                return AnalysisResult.model_validate(result.final_output)
            return _normalize_research(
                result, AgentResearchOutput.model_validate(result.final_output)
            )
        except AgentConfigurationError:
            raise
        except Exception as error:
            if research_enabled:
                raise ResearchExecutionError(
                    "Current information research could not be completed."
                ) from error
            raise AgentExecutionError("The agent could not analyze this question.") from error
