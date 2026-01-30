"""Базовый класс агента."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.models.state import InterviewState


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
        response = await self.llm.ainvoke(messages)
        return response.content

    def invoke_llm_sync(self, user_prompt: str, system_prompt: str | None = None) -> str:
        """Синхронный вызов LLM."""
        messages = [
            SystemMessage(content=system_prompt or self.get_system_prompt()),
            HumanMessage(content=user_prompt),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def format_thoughts(self, thoughts: str) -> str:
        """Форматировать мысли с префиксом имени агента."""
        return f"[{self.name}]: {thoughts}"
