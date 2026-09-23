"""Isolated Track A Jev judgments and sanitized evaluation logs."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from typesafe_sdk import Choice, ChoiceAnswer, Noul, NoulAnswer, TypeSafeClient

from spendguard.agent import load_project_env


JEV_MODEL = "jev-latest"
JudgmentId = Literal[
    "additional_information",
    "current_information_search",
    "search_result_relevance",
    "decision_result_review",
]
AutomationLevel = Literal["L0", "L1", "L2", "L3", "L4"]

JUDGMENT_DEFINITIONS = {
    "additional_information": {
        "primitive": "noul",
        "automation_level": "L2",
        "true": "The request cannot be answered usefully without at least one decision-critical detail not supplied by the user.",
        "false": "The request can be answered usefully from the supplied information, or missing details can be handled as explicit assumptions.",
    },
    "current_information_search": {
        "primitive": "noul",
        "automation_level": "L2",
        "true": "Answering requires a current external fact that can change over time, such as a current price, policy, plan, or availability.",
        "false": "The request can be answered from user-provided facts, stable knowledge, or deterministic calculation without a changing external fact.",
    },
    "search_result_relevance": {
        "primitive": "choice",
        "automation_level": "L1",
        "choices": {
            "relevant": "The result directly provides evidence useful for the user's specific current-information question.",
            "not_relevant": "The result does not materially help answer the user's specific question.",
            "unknown": "The result is ambiguous, too incomplete, or outside the covered cases; request Agent review.",
        },
    },
    "decision_result_review": {
        "primitive": "noul",
        "automation_level": "L2",
        "true": "The decision result has an unresolved ambiguity, unsupported claim, material inconsistency, or evidence gap that warrants another review.",
        "false": "The result is internally consistent, its claims are supported by the provided evidence, and no material issue requiring another review is apparent.",
    },
}


class PrototypeConfigurationError(RuntimeError):
    """Missing experimental TypeSafe configuration."""


class PrototypeExecutionError(RuntimeError):
    """A sanitized Track A judgment failure."""

    def __init__(self, judgment_id: str, cause: Exception) -> None:
        super().__init__(f"Track A judgment failed: {judgment_id}.")
        self.cause_type = type(cause).__name__
        self.status_code = getattr(cause, "status_code", None)


@dataclass(frozen=True)
class JudgmentResult:
    judgment_id: JudgmentId
    primitive: str
    typed_result: str
    score: float | None
    confidence: float | None
    abstained: bool
    latency_ms: float
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    automation_level: AutomationLevel
    selected_path: str


def build_prototype_client() -> TypeSafeClient:
    """Create the client only when the experimental entry point is invoked."""

    load_project_env()
    if not os.getenv("TYPESAFE_API_KEY"):
        raise PrototypeConfigurationError("TYPESAFE_API_KEY is required for Track A.")
    return TypeSafeClient(model=JEV_MODEL)


def _noul_question(judgment_id: JudgmentId) -> Noul:
    definition = JUDGMENT_DEFINITIONS[judgment_id]
    return Noul(
        instructions=f"Evaluate only the {judgment_id.replace('_', ' ')} judgment for this state.",
        criteria={"true": definition["true"], "false": definition["false"]},
    )


def judge(
    judgment_id: JudgmentId,
    state: dict[str, object],
    *,
    client: TypeSafeClient | object | None = None,
) -> JudgmentResult:
    """Run one isolated typed judgment. Every result remains advisory at L2."""

    api = client or build_prototype_client()
    started = time.perf_counter()
    try:
        if judgment_id == "search_result_relevance":
            response = api.system_one(
                state=state,
                questions={
                    "judgment": Choice(
                        instructions=(
                            "Judge whether this single web search result is relevant to the user's query. "
                            "Choose unknown if the result is ambiguous, incomplete, or outside the defined choices."
                        ),
                        criteria=JUDGMENT_DEFINITIONS[judgment_id]["choices"],
                    )
                },
            )
            answer = cast(ChoiceAnswer, response.answers["judgment"])
            choice = answer.choice if answer.choice in JUDGMENT_DEFINITIONS[judgment_id]["choices"] else "unknown"
            typed_result = cast(str, choice)
            score = None
            confidence = float(answer.confidence)
            abstained = typed_result == "unknown"
        else:
            response = api.system_one(
                state=state,
                questions={"judgment": _noul_question(judgment_id)},
            )
            answer = cast(NoulAnswer, response.answers["judgment"])
            score = float(answer.noul)
            confidence = None
            if score == 0.5:
                typed_result, abstained = "needs_review", True
            else:
                typed_result, abstained = ("yes" if score > 0.5 else "no"), False
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = None if input_tokens is None else input_tokens * 0.042 / 1_000_000
        level = JUDGMENT_DEFINITIONS[judgment_id]["automation_level"]
        selected_path = "agent_review" if abstained or level == "L2" else "automatic_filter"
        return JudgmentResult(
            judgment_id=judgment_id,
            primitive=JUDGMENT_DEFINITIONS[judgment_id]["primitive"],
            typed_result=typed_result,
            score=score,
            confidence=confidence,
            abstained=abstained,
            latency_ms=(time.perf_counter() - started) * 1_000,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            automation_level=cast(AutomationLevel, level),
            selected_path=selected_path,
        )
    except PrototypeExecutionError:
        raise
    except Exception as error:
        raise PrototypeExecutionError(judgment_id, error) from error


def append_sanitized_log(
    path: Path,
    *,
    case_id: str,
    result: JudgmentResult,
    expected: str | None,
    workflow_success: bool | None = None,
    selected_path: str | None = None,
) -> None:
    """Append metadata only; never persist the state or API/provider error text."""

    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "case_id": case_id,
        "judgment_id": result.judgment_id,
        "primitive": result.primitive,
        "typed_result": result.typed_result,
        "expected": expected,
        "workflow_success": workflow_success,
        "score": result.score,
        "confidence": result.confidence,
        "abstained": result.abstained,
        "latency_ms": result.latency_ms,
        "usage": {"input_tokens": result.input_tokens, "output_tokens": result.output_tokens},
        "estimated_cost_usd": result.estimated_cost_usd,
        "selected_path": selected_path or result.selected_path,
        "automation_level": result.automation_level,
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def fixture_sha256(path: Path) -> str:
    """Stable digest for the frozen Track A expected labels and inputs."""

    return hashlib.sha256(path.read_bytes()).hexdigest()
