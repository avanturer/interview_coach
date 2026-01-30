"""Агент-интервьюер — ведёт техническое интервью."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel

from src.agents.base import BaseAgent
from src.config import settings
from src.constants import QUALITY_GOOD
from src.models.state import InterviewState
from src.prompts.interviewer import (
    GREETING_TEMPLATE,
    INTERVIEWER_SYSTEM_PROMPT,
    get_interviewer_prompt,
)
from src.topics import get_topics_for_position

_META_PREFIXES = ("##", "**", "[", "observer:", "interviewer:", "инструкция:", "задача:", "фаза:")
_META_KEYWORDS = ("internal thought", "внутренние мысли", "правила:", "контекст:")


class InterviewerAgent(BaseAgent):
    """Ведёт интервью: задаёт вопросы, отвечает на встречные вопросы.

    НЕ проверяет факты (Observer) и НЕ принимает решение о найме (Evaluator).
    """

    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Interviewer")

    def get_system_prompt(self) -> str:
        return INTERVIEWER_SYSTEM_PROMPT

    async def process(self, state: InterviewState) -> dict[str, Any]:
        return await self._generate_message_async(state)

    def process_sync(self, state: InterviewState) -> dict[str, Any]:
        return self._generate_message(state)

    async def _generate_message_async(self, state: InterviewState) -> dict[str, Any]:
        if not state.get("turns"):
            return self._greeting_response(state)

        prompt = self._build_prompt(state)
        message = await self.invoke_llm(prompt)
        return self._format_response(state, self._clean_message(message))

    def _generate_message(self, state: InterviewState) -> dict[str, Any]:
        if not state.get("turns"):
            return self._greeting_response(state)

        prompt = self._build_prompt(state)
        message = self.invoke_llm_sync(prompt)
        return self._format_response(state, self._clean_message(message))

    def _greeting_response(self, state: InterviewState) -> dict[str, Any]:
        message = GREETING_TEMPLATE.format(position=state.get("position", "Developer"))
        thoughts = self.format_thoughts("Начинаю интервью. Приветствую кандидата.")
        return {
            "current_agent_message": message,
            "internal_thoughts_buffer": state.get("internal_thoughts_buffer", []) + [thoughts],
        }

    def _build_prompt(self, state: InterviewState) -> str:
        observer_analysis = state.get("current_observer_analysis")
        instruction = (
            observer_analysis.instruction_to_interviewer
            if observer_analysis
            else "Продолжай интервью, задай технический вопрос."
        )

        user_question = ""
        if observer_analysis and observer_analysis.is_question_from_user:
            user_question = observer_analysis.user_question

        should_give_hint = False
        skipped_count = len(state.get("skipped_topics", []))
        evasion_count = state.get("evasion_count", 0)
        current_ok = False
        if observer_analysis:
            current_ok = (
                observer_analysis.topic_covered
                or observer_analysis.answer_quality >= QUALITY_GOOD
            )
        if (
            skipped_count >= settings.hint_skipped_threshold
            or evasion_count >= settings.hint_evasion_threshold
        ) and not current_ok:
            should_give_hint = state.get("hints_used", 0) < settings.max_hints

        position = state.get("position", "")
        covered = state.get("covered_topics", [])
        skipped = state.get("skipped_topics", [])
        suggested_topics = self._get_suggested_topics(position, covered, skipped)

        interview_phase = state.get("interview_phase", "technical")
        turn_count = state.get("current_turn_id", 0)

        wrap_up_threshold = max(1, settings.max_turns - 2)
        if turn_count >= wrap_up_threshold and observer_analysis and observer_analysis.wants_to_end_interview:
            interview_phase = "wrap_up"

        return get_interviewer_prompt(
            position=position,
            grade=state.get("grade", ""),
            experience=state.get("experience", ""),
            covered_topics=covered,
            skipped_topics=skipped,
            candidate_mentioned=state.get("candidate_mentioned", []),
            current_difficulty=state.get("current_difficulty", 1),
            observer_instruction=instruction,
            conversation_history=self._build_history(state),
            user_question=user_question,
            should_give_hint=should_give_hint,
            suggested_topics=suggested_topics,
            interview_phase=interview_phase,
            is_first_message=False,
        )

    def _get_suggested_topics(self, position: str, covered: list[str], skipped: list[str]) -> list[str]:
        """Получить рекомендуемые темы для позиции."""
        topics_bank = get_topics_for_position(position)
        suggested = []

        for topic_key, topic in topics_bank.items():
            if topic.name not in covered and topic.name not in skipped:
                suggested.append(topic.name)

        return suggested[:5]

    def _format_response(self, state: InterviewState, message: str) -> dict[str, Any]:
        thoughts = self._generate_thoughts(state)
        return {
            "current_agent_message": message,
            "internal_thoughts_buffer": state.get("internal_thoughts_buffer", []) + [thoughts],
        }

    def _build_history(self, state: InterviewState) -> str:
        turns = state.get("turns", [])
        if not turns:
            return "Начало интервью"

        parts = []
        for turn in turns[-settings.context_window_size:]:
            parts.append(f"Интервьюер: {turn.agent_visible_message}")
            parts.append(f"Кандидат: {turn.user_message}")

        current_msg = state.get("current_user_message", "")
        if current_msg and (not turns or turns[-1].user_message != current_msg):
            parts.append(f"Кандидат: {current_msg}")

        return "\n".join(parts)

    def _clean_message(self, message: str) -> str:
        """Отфильтровать мета-текст из ответа LLM."""
        lines = []
        for line in message.strip().split("\n"):
            lower = line.lower().strip()
            if lower.startswith(_META_PREFIXES):
                continue
            if any(kw in lower for kw in _META_KEYWORDS):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    def _generate_thoughts(self, state: InterviewState) -> str:
        analysis = state.get("current_observer_analysis")
        parts = [f"Сложность: {state.get('current_difficulty', 1)}/5"]

        if analysis:
            if analysis.is_hallucination:
                parts.append("Корректирую ложный факт")
            if analysis.is_off_topic:
                parts.append("Возвращаю к теме")
            if analysis.is_question_from_user:
                parts.append("Отвечаю на вопрос кандидата")

        return self.format_thoughts(". ".join(parts))
