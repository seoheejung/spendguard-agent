"""SpendGuard API request and response schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from spendguard.calculations import CalculationResult


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
    """Structured agent response, with external research kept separate."""

    intent: Intent
    summary: str = Field(min_length=1)
    known_facts: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    research: "ResearchResult" = Field(default_factory=lambda: ResearchResult.not_needed())
    external_facts: list["ExternalFact"] = Field(default_factory=list)


ResearchStatus = Literal[
    "not_needed",
    "completed",
    "no_results",
    "official_source_unconfirmed",
    "conflicting",
    "freshness_unverifiable",
]


class ResearchResult(BaseModel):
    """Research execution information, distinct from the agent explanation."""

    needed: bool
    status: ResearchStatus
    queries: list[str] = Field(default_factory=list)
    official_source_confirmed: bool = False
    note: str = Field(min_length=1)

    @classmethod
    def not_needed(cls) -> "ResearchResult":
        return cls(
            needed=False,
            status="not_needed",
            note="This question does not require current external information.",
        )


class ExternalFact(BaseModel):
    """A current external fact with a source trace."""

    value: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    retrieved_at: str = Field(min_length=1)


class AgentExternalFact(BaseModel):
    """Agent-proposed fact retained only after source URL verification."""

    value: str = Field(min_length=1)
    source_url: str = Field(min_length=1)


class AgentResearchOutput(BaseModel):
    """Untrusted research fields emitted by the agent before source normalization."""

    intent: Intent
    summary: str = Field(min_length=1)
    known_facts: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    external_facts: list[AgentExternalFact] = Field(default_factory=list)
    official_source_urls: list[str] = Field(default_factory=list)
    conflicting_sources: bool = False
    freshness_confirmed: bool = False


class ResearchNeed(BaseModel):
    """Backend-owned decision whether a question needs current research."""

    needed: bool


class AnalyzeRequest(BaseModel):
    """Natural-language question submitted from the UI."""

    question: str = Field(min_length=1, max_length=4_000)


CalculationToolName = Literal[
    "calculate_installment",
    "calculate_refinance",
    "calculate_usage_cost",
    "annualize_expense",
    "calculate_tco",
    "compare_costs",
]


class CalculationRequest(BaseModel):
    """Existing calculation-tool request."""

    tool: CalculationToolName
    data: dict[str, Any]


class CalculationExecutionResult(BaseModel):
    """Calculation result with execution boundary."""

    tool: CalculationToolName
    execution: Literal["direct", "mcp"]
    calculation: CalculationResult
