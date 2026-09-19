from types import SimpleNamespace

import pytest
from typesafe_sdk import ChoiceAnswer

from spendguard.jev import (
    INTENT_CRITERIA,
    JevConfigurationError,
    JevExecutionError,
    JevIntentClassifier,
    JevIntentResult,
    build_jev_client,
)
from spendguard.models import AnalysisResult
from spendguard.phase2_evaluation import JevEvaluationReport, evaluate_cases


class StubClient:
    def __init__(self, choice: str = "purchase") -> None:
        self.choice = choice
        self.request: dict[str, object] | None = None
        self.closed = False

    def system_one(self, *, state: object, questions: object) -> object:
        self.request = {"state": state, "questions": questions}
        return SimpleNamespace(
            answers={
                "intent": ChoiceAnswer.model_validate(
                    {
                        "type": "choice",
                        "choice": self.choice,
                        "confidence": 0.8,
                        "probabilities": {self.choice: 1.0},
                    }
                )
            },
            usage=SimpleNamespace(input_tokens=12, output_tokens=3),
        )

    def close(self) -> None:
        self.closed = True


class FailingClient(StubClient):
    def system_one(self, *, state: object, questions: object) -> object:
        raise RuntimeError("network failure")


def test_jev_choice_candidates_match_phase_one_intents() -> None:
    expected_intents = set(AnalysisResult.model_fields["intent"].annotation.__args__)

    assert set(INTENT_CRITERIA) == expected_intents


def test_jev_classifier_converts_choice_response() -> None:
    client = StubClient()
    classifier = JevIntentClassifier(client)

    result = classifier.classify("노트북을 사도 될지 고민 중이에요.")

    assert result == JevIntentResult(
        intent="purchase",
        confidence=0.8,
        probabilities={"purchase": 1.0},
        input_tokens=12,
        output_tokens=3,
    )
    assert client.request is not None
    assert client.request["state"] == {"question": "노트북을 사도 될지 고민 중이에요."}


def test_jev_classifier_rejects_unknown_choice() -> None:
    classifier = JevIntentClassifier(StubClient(choice="new_intent"))

    with pytest.raises(JevExecutionError, match="could not classify"):
        classifier.classify("질문")


def test_jev_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setattr("spendguard.jev.load_project_env", lambda: None)

    with pytest.raises(JevConfigurationError, match="TYPESAFE_API_KEY"):
        build_jev_client()


def test_jev_sanitizes_client_error() -> None:
    classifier = JevIntentClassifier(FailingClient())

    with pytest.raises(JevExecutionError, match="could not classify"):
        classifier.classify("질문")


def test_phase_two_evaluation_report_schema() -> None:
    classifier = JevIntentClassifier(StubClient())
    report = evaluate_cases(
        [
            {
                "id": "purchase-001",
                "input": "노트북을 사도 될지 고민 중이에요.",
                "expected_intent": "purchase",
            }
        ],
        classifier,
    )

    assert isinstance(report, JevEvaluationReport)
    assert report.correct_intents == 1
    assert report.usage.input_tokens == 12
    assert report.usage.output_tokens == 3
    assert report.usage.complete is True
    assert report.cost_usd is None
