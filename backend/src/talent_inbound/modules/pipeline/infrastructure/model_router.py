"""Model router — selects LLM tier (FAST/SMART) per agent.

FAST tier: cheap and fast models for classification/pattern matching.
SMART tier: powerful models for extraction/reasoning/generation.
"""

from enum import StrEnum

from langchain_core.language_models import BaseChatModel


class ModelTier(StrEnum):
    FAST = "FAST"
    SMART = "SMART"


# Agent → tier mapping
AGENT_TIERS: dict[str, ModelTier] = {
    "guardrail": ModelTier.FAST,
    "gatekeeper": ModelTier.FAST,
    "extractor": ModelTier.SMART,
    "analyst": ModelTier.SMART,
    "communicator": ModelTier.SMART,
}


class ModelRouter:
    """Routes agents to the appropriate LLM model by tier.

    Supports OpenAI and Anthropic providers. Falls back gracefully
    when API keys are not configured (returns None → agents use mock).
    """

    def __init__(
        self,
        openai_api_key: str = "",
        anthropic_api_key: str = "",
    ) -> None:
        self._openai_key = openai_api_key
        self._anthropic_key = anthropic_api_key
        self._models: dict[ModelTier, BaseChatModel | None] = {
            ModelTier.FAST: None,
            ModelTier.SMART: None,
        }
        self._init_models()

    def _init_models(self) -> None:
        """Initialize LLM clients based on available API keys."""
        if self._openai_key:
            try:
                from langchain_openai import ChatOpenAI

                self._models[ModelTier.FAST] = ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=self._openai_key,
                    temperature=0,
                )
                self._models[ModelTier.SMART] = ChatOpenAI(
                    model="gpt-4o",
                    api_key=self._openai_key,
                    temperature=0,
                )
            except ImportError:
                pass

        if self._anthropic_key:
            try:
                from langchain_anthropic import ChatAnthropic

                self._models[ModelTier.FAST] = ChatAnthropic(
                    model="claude-haiku-4-5-20251001",
                    api_key=self._anthropic_key,
                    temperature=0,
                )
                self._models[ModelTier.SMART] = ChatAnthropic(
                    model="claude-sonnet-4-5-20250929",
                    api_key=self._anthropic_key,
                    temperature=0,
                )
            except ImportError:
                pass

    def get_model(self, agent_name: str) -> BaseChatModel | None:
        """Return the LLM for a given agent, or None if not configured."""
        tier = AGENT_TIERS.get(agent_name, ModelTier.SMART)
        return self._models.get(tier)

    @property
    def is_configured(self) -> bool:
        """True if at least one LLM provider is available."""
        return any(m is not None for m in self._models.values())
