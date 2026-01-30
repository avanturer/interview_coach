"""Агент-наблюдатель — анализирует ответы за кулисами."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.language_models import BaseChatModel

from src.agents.base import BaseAgent
from src.config import settings
from src.constants import (
    MAX_DIFFICULTY,
    MIN_DIFFICULTY,
    QUALITY_EXCELLENT,
    QUALITY_GOOD,
    QUALITY_POOR,
)
from src.models.state import InterviewState, ObserverAnalysis, SkillScore, SoftSkillsTracker
from src.prompts.observer import OBSERVER_SYSTEM_PROMPT, get_observer_prompt


class ObserverAgent(BaseAgent):
    """Анализирует ответы кандидата и даёт инструкции Interviewer."""

    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Observer")

    def get_system_prompt(self) -> str:
        return OBSERVER_SYSTEM_PROMPT

    async def process(self, state: InterviewState) -> dict[str, Any]:
        return await self._analyze_async(state)

    def process_sync(self, state: InterviewState) -> dict[str, Any]:
        return self._analyze(state)

    async def _analyze_async(self, state: InterviewState) -> dict[str, Any]:
        user_answer = state.get("current_user_message", "")
        if not user_answer:
            return {}

        prompt = self._build_prompt(state)
        response = await self.invoke_llm(prompt)
        return self._process_response(state, response)

    def _analyze(self, state: InterviewState) -> dict[str, Any]:
        user_answer = state.get("current_user_message", "")
        if not user_answer:
            return {}

        prompt = self._build_prompt(state)
        response = self.invoke_llm_sync(prompt)
        return self._process_response(state, response)

    def _build_prompt(self, state: InterviewState) -> str:
        return get_observer_prompt(
            position=state.get("position", ""),
            grade=state.get("grade", ""),
            current_question=state.get("current_agent_message", ""),
            user_answer=state.get("current_user_message", ""),
            conversation_history=self._build_history(state),
            covered_topics=state.get("covered_topics", []),
            skipped_topics=state.get("skipped_topics", []),
            current_difficulty=state.get("current_difficulty", 1),
            interview_phase=state.get("interview_phase", "technical"),
        )

    def _process_response(self, state: InterviewState, response: str) -> dict[str, Any]:
        analysis = self._parse_analysis(response)

        user_message = state.get("current_user_message", "")
        if self._check_user_stop_intent(user_message):
            analysis.wants_to_end_interview = True
            analysis.instruction_to_interviewer = "Кандидат хочет завершить. Заверши интервью."

        skill_scores = self._update_skill_scores(state.get("skill_scores", {}), analysis)
        new_difficulty = self._calculate_difficulty(state.get("current_difficulty", 1), analysis)

        covered_topics = list(state.get("covered_topics", []))
        for skill in analysis.detected_skills:
            if skill not in covered_topics:
                covered_topics.append(skill)

        skipped_topics = list(state.get("skipped_topics", []))
        if analysis.wants_to_skip and analysis.current_topic:
            if analysis.current_topic not in skipped_topics:
                skipped_topics.append(analysis.current_topic)

        evasion_count = state.get("evasion_count", 0)
        hallucination_count = state.get("hallucination_count", 0)
        confident_nonsense_count = state.get("confident_nonsense_count", 0)
        overqualified_signals = state.get("overqualified_signals", 0)
        underqualified_signals = state.get("underqualified_signals", 0)
        spam_count = state.get("spam_count", 0)

        if analysis.is_evasive:
            evasion_count += 1
        if analysis.is_hallucination:
            hallucination_count += 1
        if analysis.is_confident_nonsense:
            confident_nonsense_count += 1
        if analysis.is_spam_or_troll:
            spam_count += 1
        if analysis.grade_mismatch == "overqualified":
            overqualified_signals += 1
        elif analysis.grade_mismatch == "underqualified":
            underqualified_signals += 1

        soft_tracker = state.get("soft_skills_tracker") or SoftSkillsTracker()
        soft_tracker.clarity_scores.append(analysis.clarity_score)
        if analysis.showed_honesty:
            soft_tracker.honesty_signals.append("honest_admission")
        if analysis.showed_engagement:
            soft_tracker.engagement_signals.append("showed_interest")
        if analysis.is_confident_nonsense:
            soft_tracker.red_flags.append("confident_nonsense")
        if analysis.is_evasive and evasion_count >= 3:
            soft_tracker.red_flags.append("repeated_evasion")
        if analysis.is_spam_or_troll:
            soft_tracker.red_flags.append("spam_or_troll")

        thoughts = self._format_detailed_thoughts(analysis, state)

        candidate_mentioned = list(state.get("candidate_mentioned", []))
        for info in analysis.mentioned_info:
            if info and info not in candidate_mentioned:
                candidate_mentioned.append(info)

        return {
            "current_observer_analysis": analysis,
            "skill_scores": skill_scores,
            "current_difficulty": new_difficulty,
            "covered_topics": covered_topics,
            "skipped_topics": skipped_topics,
            "candidate_mentioned": candidate_mentioned,
            "evasion_count": evasion_count,
            "hallucination_count": hallucination_count,
            "confident_nonsense_count": confident_nonsense_count,
            "spam_count": spam_count,
            "overqualified_signals": overqualified_signals,
            "underqualified_signals": underqualified_signals,
            "soft_skills_tracker": soft_tracker,
            "internal_thoughts_buffer": [thoughts],
        }

    def _format_detailed_thoughts(self, analysis: ObserverAnalysis, state: InterviewState) -> str:
        """Форматировать внутренние мысли для логирования (формат инструкции: [agent]: thought\\n)."""
        lines = [f"[Observer]: Качество: {analysis.answer_quality}/10"]

        if analysis.is_hallucination:
            lines.append("[Observer]: Галлюцинация")
        if analysis.is_confident_nonsense:
            lines.append("[Observer]: Уверенный бред")
        if analysis.is_evasive:
            lines.append("[Observer]: Уклонение")
        if analysis.is_spam_or_troll:
            lines.append("[Observer]: Спам")
        if analysis.grade_mismatch != "none":
            lines.append(f"[Observer]: Grade mismatch: {analysis.grade_mismatch}")

        lines.append(f"[Observer]: {analysis.instruction_to_interviewer}")

        if analysis.thoughts:
            lines.append(f"[Observer]: {analysis.thoughts}")

        return "\n".join(lines)

    def _build_history(self, state: InterviewState) -> str:
        turns = state.get("turns", [])
        if not turns:
            return "Начало интервью"

        parts = []
        for turn in turns[-settings.context_window_size:]:
            parts.append(f"Интервьюер: {turn.agent_visible_message}")
            parts.append(f"Кандидат: {turn.user_message}")
        return "\n".join(parts)

    def _parse_analysis(self, response: str) -> ObserverAnalysis:
        """Извлечь и распарсить JSON из ответа LLM."""
        try:
            match = re.search(r"\{[\s\S]*\}", response)
            data = json.loads(match.group() if match else response)

            def clamp(val, min_v, max_v, default):
                try:
                    return max(min_v, min(max_v, int(val) if val else default))
                except (ValueError, TypeError):
                    return default

            answer_quality = clamp(data.get("answer_quality"), 1, 10, 5)
            clarity_score = clamp(data.get("clarity_score"), 1, 10, 5)

            grade_mismatch_raw = data.get("grade_mismatch", "none")
            grade_mismatch = grade_mismatch_raw if grade_mismatch_raw in ("none", "overqualified", "underqualified") else "none"

            return ObserverAnalysis(
                wants_to_end_interview=data.get("wants_to_end_interview", False),
                wants_to_skip=data.get("wants_to_skip", False),
                topic_covered=data.get("topic_covered", False),
                current_topic=data.get("current_topic", ""),
                is_evasive=data.get("is_evasive", False),
                is_confident_nonsense=data.get("is_confident_nonsense", False),
                is_spam_or_troll=data.get("is_spam_or_troll", False),
                grade_mismatch=grade_mismatch,
                is_valid_answer=data.get("is_valid_answer", True),
                is_hallucination=data.get("is_hallucination", False),
                is_off_topic=data.get("is_off_topic", False),
                is_question_from_user=data.get("is_question_from_user", False),
                user_question=data.get("user_question", ""),
                answer_quality=answer_quality,
                detected_skills=data.get("detected_skills", []),
                instruction_to_interviewer=data.get(
                    "instruction_to_interviewer", "Продолжай интервью."
                ),
                thoughts=data.get("thoughts", "Анализ завершён."),
                clarity_score=clarity_score,
                showed_honesty=data.get("showed_honesty", False),
                showed_engagement=data.get("showed_engagement", False),
                mentioned_info=data.get("mentioned_info", []),
            )
        except (json.JSONDecodeError, KeyError, AttributeError, ValueError, TypeError) as e:
            return ObserverAnalysis(
                wants_to_end_interview=False,
                wants_to_skip=False,
                is_valid_answer=True,
                answer_quality=5,
                instruction_to_interviewer="Продолжай интервью, задай следующий технический вопрос.",
                thoughts=f"Ошибка парсинга: {e}. Продолжаем.",
            )

    def _check_user_stop_intent(self, user_message: str) -> bool:
        """Проверить, хочет ли пользователь завершить интервью."""
        msg_lower = user_message.lower().strip()

        explicit_stops = (
            "стоп", "stop", "хватит", "закончим", "всё", "конец",
            "финиш", "заканчиваем", "завершаем", "достаточно", "пока",
        )

        if len(msg_lower) < 50:
            for stop in explicit_stops:
                if stop in msg_lower:
                    return True

        if "давай фидбэк" in msg_lower or "дай фидбэк" in msg_lower:
            return True

        return False

    def _update_skill_scores(
        self,
        scores: dict[str, SkillScore],
        analysis: ObserverAnalysis,
    ) -> dict[str, SkillScore]:
        updated = dict(scores)

        for skill in analysis.detected_skills:
            if skill not in updated:
                updated[skill] = SkillScore(topic=skill)

            s = updated[skill]
            if analysis.answer_quality >= QUALITY_GOOD:
                s.correct_answers += 1
                s.score = min(10, s.score + 1)
            elif analysis.answer_quality <= QUALITY_POOR:
                s.incorrect_answers += 1
                s.score = max(0, s.score - 1)

            if analysis.is_hallucination:
                s.notes.append("Галлюцинация")

            updated[skill] = s

        return updated

    def _calculate_difficulty(self, current: int, analysis: ObserverAnalysis) -> int:
        adjust = getattr(analysis, "should_adjust_difficulty", None)
        quality = analysis.answer_quality

        if adjust == "up" and quality >= QUALITY_GOOD:
            return min(MAX_DIFFICULTY, current + 1)
        if adjust == "down" and quality <= QUALITY_POOR:
            return max(MIN_DIFFICULTY, current - 1)
        if quality >= QUALITY_EXCELLENT:
            return min(MAX_DIFFICULTY, current + 1)
        if quality <= QUALITY_POOR:
            return max(MIN_DIFFICULTY, current - 1)

        return current
