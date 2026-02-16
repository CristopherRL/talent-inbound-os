"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve paths relative to the backend directory, not the CWD
_BACKEND_DIR = (
    Path(__file__).resolve().parents[2]
)  # src/talent_inbound -> src -> backend


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://talent:talent_dev@localhost:5432/talent_inbound"
    )

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    jwt_secret_key: str = "change-me-generate-with-openssl-rand-hex-32"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # LLM Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # LLM Model configuration
    llm_provider: str = "anthropic"  # "anthropic" | "openai"
    llm_fast_model: str = "claude-haiku-4-5-20251001"
    llm_smart_model: str = "claude-sonnet-4-5-20250929"

    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "talent-inbound-os"

    # Application
    log_level: str = "INFO"
    environment: str = "development"
    upload_dir: str = str(_BACKEND_DIR / "uploads")

    # Ingestion
    max_message_length: int = 50000

    # Extraction — fields required for a complete extraction (missing = INCOMPLETE_INFO)
    extraction_required_fields: list[str] = ["salary_range", "tech_stack", "role_title"]

    @property
    def pipeline_steps(self) -> list[str]:
        """Ordered agent sequence — derived from model_router.PIPELINE_STEPS (single source of truth)."""
        from talent_inbound.modules.pipeline.infrastructure.model_router import (
            PIPELINE_STEPS,
        )

        return PIPELINE_STEPS

    # Scoring weights (Analyst agent)
    scoring_base: int = 50
    scoring_skills_weight: int = 30
    scoring_work_model_match: int = 10
    scoring_work_model_mismatch: int = -5
    scoring_salary_meets_min: int = 10
    scoring_salary_below_min: int = -10

    # Scoring thresholds (classify score into high / medium / low)
    scoring_threshold_high: int = 70
    scoring_threshold_medium: int = 40

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
