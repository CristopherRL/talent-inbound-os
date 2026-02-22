"""Model router — selects LLM tier (FAST/SMART) per agent.

FAST tier: cheap and fast models for classification/pattern matching.
SMART tier: powerful models for extraction/reasoning/generation.

Model names and provider are configured via .env / Settings:
  LLM_PROVIDER=anthropic          # "anthropic" | "openai"
  LLM_FAST_MODEL=claude-haiku-4-5-20251001
  LLM_SMART_MODEL=claude-sonnet-4-5-20250929
"""

from enum import StrEnum

from langchain_core.language_models import BaseChatModel


class ModelTier(StrEnum):
    FAST = "FAST"
    SMART = "SMART"


# Agent → tier mapping (ordered: defines the canonical pipeline step sequence)
AGENT_TIERS: dict[str, ModelTier] = {
    "guardrail": ModelTier.FAST,
    "gatekeeper": ModelTier.FAST,
    "extractor": ModelTier.SMART,
    "language_detector": ModelTier.FAST,
    "analyst": ModelTier.SMART,
    "communicator": ModelTier.SMART,
    "stage_detector": ModelTier.FAST,
}

# Canonical ordered list of pipeline steps — derived from AGENT_TIERS.
# This is the single source of truth. Import it wherever you need the step list.
PIPELINE_STEPS: list[str] = list(AGENT_TIERS.keys())


class ModelRouter:
    """Routes agents to the appropriate LLM model by tier.

    Supports OpenAI and Anthropic providers. The provider and model names
    are read from Settings (config.py / .env) so you can switch without
    touching code.
    """

    def __init__(
        self,
        openai_api_key: str = "",
        anthropic_api_key: str = "",
        provider: str = "anthropic",
        fast_model: str = "claude-haiku-4-5-20251001",
        smart_model: str = "claude-sonnet-4-5-20250929",
    ) -> None:
        self._openai_key = openai_api_key
        self._anthropic_key = anthropic_api_key
        self._provider = provider.lower()
        self._fast_model = fast_model
        self._smart_model = smart_model
        self._models: dict[ModelTier, BaseChatModel | None] = {
            ModelTier.FAST: None,
            ModelTier.SMART: None,
        }
        self._init_models()

    def _init_models(self) -> None:
        """Initialize LLM clients based on the configured provider."""
        if self._provider == "openai" and self._openai_key:
            try:
                from langchain_openai import ChatOpenAI

                self._models[ModelTier.FAST] = ChatOpenAI(
                    model=self._fast_model,
                    api_key=self._openai_key,
                    temperature=0,
                )
                self._models[ModelTier.SMART] = ChatOpenAI(
                    model=self._smart_model,
                    api_key=self._openai_key,
                    temperature=0,
                )
            except ImportError:
                pass

        elif self._provider == "anthropic" and self._anthropic_key:
            try:
                from langchain_anthropic import ChatAnthropic

                self._models[ModelTier.FAST] = ChatAnthropic(
                    model=self._fast_model,
                    api_key=self._anthropic_key,
                    temperature=0,
                )
                self._models[ModelTier.SMART] = ChatAnthropic(
                    model=self._smart_model,
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
