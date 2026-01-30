"""Base agent class for Interview Coach multi-agent system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.models.state import InterviewState


class BaseAgent(ABC):
    """Abstract base for all interview agents."""

    __slots__ = ("llm", "name")

    def __init__(self, llm: BaseChatModel, name: str):
        self.llm = llm
        self.name = name

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return agent's system prompt."""

    @abstractmethod
    async def process(self, state: InterviewState) -> dict[str, Any]:
        """Process state and return updates."""

    async def invoke_llm(self, user_prompt: str, system_prompt: str | None = None) -> str:
        """Async LLM invocation."""
        messages = [
            SystemMessage(content=system_prompt or self.get_system_prompt()),
            HumanMessage(content=user_prompt),
        ]
        response = await self.llm.ainvoke(messages)
        return response.content

    def invoke_llm_sync(self, user_prompt: str, system_prompt: str | None = None) -> str:
        """Sync LLM invocation."""
        messages = [
            SystemMessage(content=system_prompt or self.get_system_prompt()),
            HumanMessage(content=user_prompt),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def format_thoughts(self, thoughts: str) -> str:
        """Format thoughts with agent name prefix for logging."""
        return f"[{self.name}]: {thoughts}"
