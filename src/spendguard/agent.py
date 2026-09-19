"""Single OpenAI agent used by the Phase 1 baseline."""

import os
from pathlib import Path

from agents import Agent, Runner

from spendguard.models import AnalysisResult


class AgentConfigurationError(RuntimeError):
    """Missing required OpenAI configuration."""


class AgentExecutionError(RuntimeError):
    """OpenAI agent run failed."""


INSTRUCTIONS = """
You are SpendGuard's Phase 1 intake agent. Analyze one Korean or English consumer
spending question. Return only the required structured output.

Classify intent as exactly one of:
- purchase: buying a product, used product, replacement, or purchase timing
- recurring_cost: subscription, communication bill, or other recurring expense
- finance_cost: loan, interest, refinancing, or finance cost question
- ownership_cost: vehicle or other asset ownership expense
- quote_audit: quote, estimate, or contract-cost review
- budget_optimization: household budget, spending reduction, or budget planning
- unknown: ambiguous, unrelated, or outside those categories

Extract only facts stated by the user. Do not invent current prices, policies,
calculations, sources, recommendations, or facts. List the information needed
to understand the request but absent from it in missing_fields. State any
interpretive assumption separately in assumptions. This phase does not calculate,
search the web, call tools, use MCP, or make a purchase decision.
""".strip()


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


def build_agent() -> Agent:
    """Create the sole Phase 1 agent with a Pydantic output contract."""

    load_project_env()
    model = os.getenv("OPENAI_MODEL")
    if not model:
        raise AgentConfigurationError("OPENAI_MODEL is required.")
    if not os.getenv("OPENAI_API_KEY"):
        raise AgentConfigurationError("OPENAI_API_KEY is required.")

    return Agent(
        name="SpendGuard Core Agent",
        instructions=INSTRUCTIONS,
        model=model,
        output_type=AnalysisResult,
    )


class OpenAIAnalyzer:
    """Adapter that runs the configured OpenAI Agent SDK agent."""

    async def analyze(self, question: str) -> AnalysisResult:
        try:
            result = await Runner.run(build_agent(), question)
            return AnalysisResult.model_validate(result.final_output)
        except AgentConfigurationError:
            raise
        except Exception as error:
            raise AgentExecutionError("The agent could not analyze this question.") from error
