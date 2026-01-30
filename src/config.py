"""Конфигурация приложения."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: Literal["mistral", "openai"] = "mistral"
    mistral_api_key: str | None = None
    openai_api_key: str | None = None
    llm_model: str = "mistral-large-latest"

    max_turns: int = 10
    default_difficulty: int = 1
    context_window_size: int = 5
    log_dir: Path = Path("logs")

    max_spam_count: int = 3
    max_evasion_count: int = 5

    temp_interviewer: float = 0.7
    temp_observer: float = 0.3
    temp_evaluator: float = 0.5


settings = Settings()
