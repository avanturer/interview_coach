"""Базовый класс агента."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.models.state import InterviewState


class LLMAPIError(Exception):
    """Ошибка вызова LLM API (сеть, 502, 429 и т.д.)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BaseAgent(ABC):
    """Абстрактный базовый класс для агентов интервью."""

    __slots__ = ("llm", "name")

    def __init__(self, llm: BaseChatModel, name: str):
        self.llm = llm
        self.name = name

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Вернуть системный промпт агента."""

    @abstractmethod
    async def process(self, state: InterviewState) -> dict[str, Any]:
        """Обработать состояние и вернуть обновления."""

    async def invoke_llm(self, user_prompt: str, system_prompt: str | None = None) -> str:
        """Асинхронный вызов LLM."""
        messages = [
            SystemMessage(content=system_prompt or self.get_system_prompt()),
            HumanMessage(content=user_prompt),
        ]
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            self._reraise_api_error(e)

    def invoke_llm_sync(self, user_prompt: str, system_prompt: str | None = None) -> str:
        """Синхронный вызов LLM."""
        messages = [
            SystemMessage(content=system_prompt or self.get_system_prompt()),
            HumanMessage(content=user_prompt),
        ]
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            self._reraise_api_error(e)

    def _reraise_api_error(self, e: Exception) -> None:
        """Преобразовать ошибку API в LLMAPIError с понятным сообщением."""
        status_code = None
        if hasattr(e, "response") and e.response is not None:
            status_code = getattr(e.response, "status_code", None)
        msg = str(e)
        if status_code in (500, 502, 503) or "502" in msg or "503" in msg or "500" in msg:
            raise LLMAPIError(
                f"Ошибка API (временная, код {status_code or '5xx'}). "
                "Попробуйте через несколько минут или переключитесь на OpenAI в .env"
            ) from e
        if status_code == 429 or "429" in msg:
            raise LLMAPIError(
                "Превышен лимит запросов (429). Подождите или переключитесь на другой провайдер в .env"
            ) from e
        raise LLMAPIError(f"Ошибка вызова LLM: {msg[:300]}") from e

    def format_thoughts(self, thoughts: str) -> str:
        """Форматировать мысли с префиксом имени агента."""
        return f"[{self.name}]: {thoughts}"
