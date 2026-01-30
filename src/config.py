"""Configuration management for Interview Coach."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Provider
    llm_provider: Literal["mistral", "openai"] = "mistral"

    # API Keys
    mistral_api_key: str | None = None
    openai_api_key: str | None = None

    # Model Configuration
    llm_model: str = "mistral-large-latest"

    # Interview Settings
    max_turns: int = 10
    default_difficulty: int = 1
    log_dir: Path = Path("logs")


# Global settings instance
settings = Settings()
