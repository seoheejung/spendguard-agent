"""Phase 2 Jev evaluation aggregation."""

import statistics
import time
from typing import Callable

from pydantic import BaseModel

from spendguard.jev import JevExecutionError, JevIntentClassifier, JevIntentResult
from spendguard.models import Intent


PHASE1_BASELINE = {
    "total_cases": 17,
    "correct_intents": 16,
    "accuracy": 16 / 17,
    "api_errors": 0,
    "mean_latency_ms": None,
    "cost_usd": None,
}


class JevOutcome(BaseModel):
    """One fixed-case Jev evaluation outcome."""

    id: str
    expected_intent: Intent
    actual_intent: Intent | None
    latency_ms: float
    correct: bool
    confidence: float | None = None
    probabilities: dict[Intent, float] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class JevApiError(BaseModel):
    """Sanitized Jev API error."""

    id: str
    error_type: str
    message: str


class JevUsage(BaseModel):
    """Aggregated TypeSafe token usage."""

    input_tokens: int | None
    output_tokens: int | None
    complete: bool


class JevEvaluationReport(BaseModel):
    """Fixed-case Jev evaluation report."""

    total_cases: int
    correct_intents: int
    accuracy: float
    mean_latency_ms: float | None
    p50_latency_ms: float | None
    total_duration_ms: float
    failures: list[JevOutcome]
    api_errors: list[JevApiError]
    usage: JevUsage
    cost_usd: None = None
    cost_status: str
    phase1_baseline: dict[str, int | float | None]
    comparison_notes: list[str]
    evaluation_success: bool


def _intent_answer(answer: JevIntentResult) -> tuple[Intent, dict[Intent, float]]:
    """Typed Choice conversion."""

    return answer.intent, answer.probabilities


def evaluate_cases(
    cases: list[dict[str, str]],
    classifier: JevIntentClassifier,
    clock: Callable[[], float] = time.perf_counter,
) -> JevEvaluationReport:
    """Fixed Phase 1 case evaluation."""

    started_at = clock()
    outcomes: list[JevOutcome] = []
    api_errors: list[JevApiError] = []
    input_tokens: list[int] = []
    output_tokens: list[int] = []

    for case in cases:
        case_started_at = clock()
        try:
            answer = classifier.classify(case["input"])
            actual_intent, probabilities = _intent_answer(answer)
        except JevExecutionError as error:
            outcomes.append(
                JevOutcome(
                    id=case["id"],
                    expected_intent=case["expected_intent"],
                    actual_intent=None,
                    latency_ms=(clock() - case_started_at) * 1_000,
                    correct=False,
                )
            )
            api_errors.append(
                JevApiError(
                    id=case["id"],
                    error_type=type(error.__cause__).__name__ if error.__cause__ else type(error).__name__,
                    message=str(error),
                )
            )
            continue

        latency_ms = (clock() - case_started_at) * 1_000
        outcomes.append(
            JevOutcome(
                id=case["id"],
                expected_intent=case["expected_intent"],
                actual_intent=actual_intent,
                latency_ms=latency_ms,
                correct=actual_intent == case["expected_intent"],
                confidence=answer.confidence,
                probabilities=probabilities,
                input_tokens=answer.input_tokens,
                output_tokens=answer.output_tokens,
            )
        )
        if answer.input_tokens is not None:
            input_tokens.append(answer.input_tokens)
        if answer.output_tokens is not None:
            output_tokens.append(answer.output_tokens)

    latencies = [outcome.latency_ms for outcome in outcomes]
    correct = sum(outcome.correct for outcome in outcomes)
    return JevEvaluationReport(
        total_cases=len(outcomes),
        correct_intents=correct,
        accuracy=correct / len(outcomes) if outcomes else 0,
        mean_latency_ms=statistics.mean(latencies) if latencies else None,
        p50_latency_ms=statistics.median(latencies) if latencies else None,
        total_duration_ms=(clock() - started_at) * 1_000,
        failures=[outcome for outcome in outcomes if not outcome.correct],
        api_errors=api_errors,
        usage=JevUsage(
            input_tokens=sum(input_tokens) if input_tokens else None,
            output_tokens=sum(output_tokens) if output_tokens else None,
            complete=len(input_tokens) == len(outcomes) and len(output_tokens) == len(outcomes),
        ),
        cost_status="not calculated: verified official pricing unavailable",
        phase1_baseline=PHASE1_BASELINE,
        comparison_notes=[
            "Accuracy and API errors use the same 17 fixed cases.",
            "Phase 1 did not record latency or usage, so latency and cost are not directly comparable.",
        ],
        evaluation_success=len(api_errors) == 0 and len(outcomes) == len(cases),
    )
