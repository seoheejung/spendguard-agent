"""Four optional narrow spending judgments made with Jev."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from typesafe_sdk import Choice, ChoiceAnswer, TypeSafeClient


Candidate = Literal["subscription_audit", "quote_audit", "annual_leaks", "purchase_review"]
JUDGMENTS: dict[Candidate, str] = {
    "subscription_audit": "Is this subscription a duplicate or underused savings candidate?",
    "quote_audit": "Does this quote line item need additional review?",
    "annual_leaks": "Is this expense a savings candidate with low impact on satisfaction?",
    "purchase_review": "Is this alternative worth detailed comparison?",
}
CHOICES = {
    "yes": "The supplied evidence supports the narrow candidate judgment.",
    "no": "The supplied evidence does not support the narrow candidate judgment.",
    "unknown": "The supplied evidence is insufficient or ambiguous for this narrow judgment.",
}


class JevError(RuntimeError):
    """A narrow judgment could not be obtained."""


@dataclass(frozen=True)
class JevJudgment:
    candidate: Candidate
    item: str
    choice: Literal["yes", "no", "unknown"]
    confidence: float
    latency_ms: int

    def as_prompt(self) -> str:
        return (
            f"Question: {JUDGMENTS[self.candidate]}\n"
            f"Candidate item: {self.item}\n"
            f"Jev classification: {self.choice}. "
            "Treat unknown as uncertain. Do not classify this item again. "
            "Use this only as one input to your broader recommendation."
        )

    def as_metadata(self) -> dict:
        return {
            "candidate": self.candidate,
            "item": self.item,
            "choice": self.choice,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
        }


def _load_key() -> None:
    if os.getenv("TYPESAFE_API_KEY"):
        return
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("TYPESAFE_API_KEY="):
                value = line.partition("=")[2].strip().strip('"').strip("'")
                if value:
                    os.environ["TYPESAFE_API_KEY"] = value
                break
    if not os.getenv("TYPESAFE_API_KEY"):
        raise JevError("TYPESAFE_API_KEY is required for Jev evaluation mode.")


def _judge(candidate: Candidate, question: str, item: str) -> JevJudgment:
    _load_key()
    started = time.perf_counter()
    client = TypeSafeClient(model="jev-latest")
    try:
        response = client.system_one(
            state={"user_question": question, "candidate_item": item},
            questions={
                "judgment": Choice(
                    instructions=(
                        JUDGMENTS[candidate]
                        + " Judge only the supplied candidate item using the user's stated facts. "
                        "Do not infer missing usage, prices, satisfaction, or market facts."
                    ),
                    criteria=CHOICES,
                )
            },
        )
        answer = response.answers["judgment"]
        if not isinstance(answer, ChoiceAnswer) or answer.choice not in CHOICES:
            raise JevError("Jev returned an invalid narrow judgment.")
        return JevJudgment(candidate, item, answer.choice, float(answer.confidence), round((time.perf_counter() - started) * 1000))
    except JevError:
        raise
    except Exception as error:
        raise JevError("Jev narrow judgment failed.") from error
    finally:
        client.close()


async def judge_candidate(candidate: Candidate, question: str, item: str) -> JevJudgment:
    return await asyncio.to_thread(_judge, candidate, question, item)
