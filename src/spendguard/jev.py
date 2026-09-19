"""TypeSafe Jev intent classification for the Phase 2 evaluation."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, cast

from typesafe_sdk import Choice, ChoiceAnswer, TypeSafeClient

from spendguard.agent import load_project_env
from spendguard.models import Intent


JEV_MODEL = "jev-latest"
INTENT_CRITERIA: dict[Intent, str] = {
    "purchase": "Buying a product, choosing used or new, considering a replacement, or purchase timing.",
    "recurring_cost": "A subscription, communication bill, or other repeating expense.",
    "finance_cost": "A loan, interest, refinancing, installment, or other finance cost.",
    "ownership_cost": "The ongoing cost of owning a vehicle or another long-lived asset.",
    "quote_audit": "Reviewing a quote, estimate, repair quote, contract cost, or its line items.",
    "budget_optimization": "Household budgeting, reducing spending, or planning a budget across expenses.",
    "unknown": "Ambiguous, unrelated, or outside the six other consumer spending categories.",
}
INTENT_INSTRUCTIONS = (
    "Classify the user's consumer spending question as exactly one intent. "
    "Use unknown when the question is ambiguous, unrelated, or does not clearly fit another option."
)


class JevConfigurationError(RuntimeError):
    """Missing required TypeSafe configuration."""


class JevExecutionError(RuntimeError):
    """TypeSafe Jev request failure."""


class SystemOneClient(Protocol):
    """Required TypeSafe client operation."""

    def system_one(self, *, state: object, questions: object) -> object: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class JevIntentResult:
    """Typed Jev intent response."""

    intent: Intent
    confidence: float
    probabilities: dict[Intent, float]
    input_tokens: int | None
    output_tokens: int | None


def build_jev_client() -> TypeSafeClient:
    """TypeSafe client configuration."""

    load_project_env()
    if not os.getenv("TYPESAFE_API_KEY"):
        raise JevConfigurationError("TYPESAFE_API_KEY is required.")
    return TypeSafeClient(model=JEV_MODEL)


class JevIntentClassifier:
    """Choice-only Jev classifier for offline evaluation."""

    def __init__(self, client: SystemOneClient | None = None) -> None:
        self._client = client or build_jev_client()

    def classify(self, question: str) -> JevIntentResult:
        """Intent Choice request."""

        try:
            response = self._client.system_one(
                state={"question": question},
                questions={
                    "intent": Choice(
                        instructions=INTENT_INSTRUCTIONS,
                        criteria=INTENT_CRITERIA,
                    ),
                },
            )
            answer = cast(Mapping[str, object], response.answers)["intent"]
            if not isinstance(answer, ChoiceAnswer) or answer.choice not in INTENT_CRITERIA:
                raise ValueError("Invalid intent Choice response.")
            return JevIntentResult(
                intent=cast(Intent, answer.choice),
                confidence=answer.confidence,
                probabilities=cast(dict[Intent, float], dict(answer.probabilities)),
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
        except JevExecutionError:
            raise
        except Exception as error:
            raise JevExecutionError("The Jev classifier could not classify this question.") from error

    def close(self) -> None:
        """Client resource release."""

        self._client.close()
