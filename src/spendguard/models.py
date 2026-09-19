"""Phase 1 request and response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


Intent = Literal[
    "purchase",
    "recurring_cost",
    "finance_cost",
    "ownership_cost",
    "quote_audit",
    "budget_optimization",
    "unknown",
]


class AnalysisResult(BaseModel):
    """Structured baseline response returned by the agent."""

    intent: Intent
    summary: str = Field(min_length=1)
    known_facts: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    """Natural-language question submitted from the UI."""

    question: str = Field(min_length=1, max_length=4_000)
