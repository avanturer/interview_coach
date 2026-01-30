"""Агент-оценщик — генерирует финальный фидбэк."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.language_models import BaseChatModel

from src.agents.base import BaseAgent
from src.models.feedback import (
    BehaviorAnalysis,
    Decision,
    FinalFeedback,
    HardSkillsAnalysis,
    KnowledgeGap,
    RoadmapItem,
    SoftSkillsAnalysis,
)
from src.models.state import InterviewState
from src.prompts.evaluator import EVALUATOR_SYSTEM_PROMPT, get_evaluator_prompt


class EvaluatorAgent(BaseAgent):
    """Генерирует финальный фидбэк: грейд, рекомендация, анализ навыков, roadmap.

    Анализирует ВСЕ ходы интервью для комплексной оценки.
    """

    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Evaluator")

    def get_system_prompt(self) -> str:
        return EVALUATOR_SYSTEM_PROMPT

    async def process(self, state: InterviewState) -> dict[str, Any]:
        feedback = await self._generate_async(state)
        return {"final_feedback": feedback.model_dump(), "is_finished": True, "finish_reason": "evaluation_complete"}

    def process_sync(self, state: InterviewState) -> dict[str, Any]:
        feedback = self._generate(state)
        return {"final_feedback": feedback.model_dump(), "is_finished": True, "finish_reason": "evaluation_complete"}

    async def _generate_async(self, state: InterviewState) -> FinalFeedback:
        prompt = self._build_prompt(state)
        response = await self.invoke_llm(prompt)
        return self._parse_feedback(response, state)

    def _generate(self, state: InterviewState) -> FinalFeedback:
        prompt = self._build_prompt(state)
        response = self.invoke_llm_sync(prompt)
        return self._parse_feedback(response, state)

    def _build_prompt(self, state: InterviewState) -> str:
        behavior_stats = {
            "evasion_count": state.get("evasion_count", 0),
            "hallucination_count": state.get("hallucination_count", 0),
            "confident_nonsense_count": state.get("confident_nonsense_count", 0),
            "overqualified_signals": state.get("overqualified_signals", 0),
            "underqualified_signals": state.get("underqualified_signals", 0),
            "hints_used": state.get("hints_used", 0),
        }

        soft_tracker = state.get("soft_skills_tracker")
        soft_skills_data = None
        if soft_tracker:
            soft_skills_data = {
                "clarity_scores": soft_tracker.clarity_scores if hasattr(soft_tracker, 'clarity_scores') else [],
                "honesty_signals": soft_tracker.honesty_signals if hasattr(soft_tracker, 'honesty_signals') else [],
                "engagement_signals": soft_tracker.engagement_signals if hasattr(soft_tracker, 'engagement_signals') else [],
                "red_flags": soft_tracker.red_flags if hasattr(soft_tracker, 'red_flags') else [],
            }

        return get_evaluator_prompt(
            position=state.get("position", ""),
            target_grade=state.get("grade", ""),
            experience=state.get("experience", ""),
            conversation_history=self._build_history(state),
            skill_scores=state.get("skill_scores", {}),
            total_turns=len(state.get("turns", [])),
            behavior_stats=behavior_stats,
            soft_skills_data=soft_skills_data,
        )

    def _build_history(self, state: InterviewState) -> str:
        turns = state.get("turns", [])
        if not turns:
            return "Интервью не содержит диалогов."

        parts = []
        for turn in turns:
            parts.extend([
                f"[Ход {turn.turn_id}]",
                f"Интервьюер: {turn.agent_visible_message}",
                f"Кандидат: {turn.user_message}",
                "",
            ])
        return "\n".join(parts)

    def _parse_feedback(self, response: str, state: InterviewState) -> FinalFeedback:
        """Распарсить JSON-фидбэк из ответа LLM."""
        try:
            match = re.search(r"\{[\s\S]*\}", response)
            data = json.loads(match.group() if match else response)

            def _clamp(val: int | float, lo: int, hi: int, default: int) -> int:
                try:
                    return max(lo, min(hi, int(val)))
                except (ValueError, TypeError):
                    return default

            decision_data = data.get("decision", {})
            grade_match_raw = decision_data.get("grade_match", "match")
            grade_match = grade_match_raw if grade_match_raw in ("match", "overqualified", "underqualified") else "match"

            decision = Decision(
                assessed_grade=decision_data.get("assessed_grade", state.get("grade", "Junior")),
                target_grade=decision_data.get("target_grade", state.get("grade", "")),
                hiring_recommendation=decision_data.get("hiring_recommendation", "No Hire"),
                confidence_score=_clamp(decision_data.get("confidence_score", 50), 0, 100, 50),
                grade_match=grade_match,
                summary=decision_data.get("summary", "Оценка не завершена."),
            )

            behavior_data = data.get("behavior", {})
            behavior = BehaviorAnalysis(
                evasion_count=int(behavior_data.get("evasion_count", state.get("evasion_count", 0))),
                hallucination_count=int(behavior_data.get("hallucination_count", state.get("hallucination_count", 0))),
                confident_nonsense_count=int(behavior_data.get("confident_nonsense_count", state.get("confident_nonsense_count", 0))),
                hints_used=int(behavior_data.get("hints_used", state.get("hints_used", 0))),
                notes=behavior_data.get("notes", []),
            )

            hard_data = data.get("hard_skills", {})
            gaps = [
                KnowledgeGap(
                    topic=g.get("topic", "Unknown"),
                    question_asked=g.get("question_asked", g.get("question", "")),
                    candidate_answer=g.get("candidate_answer", ""),
                    correct_answer=g.get("correct_answer", ""),
                    severity=g.get("severity", "medium"),
                )
                for g in hard_data.get("knowledge_gaps", [])
            ]
            hard_skills = HardSkillsAnalysis(
                confirmed_skills=hard_data.get("confirmed_skills", []),
                knowledge_gaps=gaps,
                technical_depth=_clamp(hard_data.get("technical_depth", 5), 1, 10, 5),
                notes=hard_data.get("notes", ""),
            )

            soft_data = data.get("soft_skills", {})
            soft_skills = SoftSkillsAnalysis(
                clarity=_clamp(soft_data.get("clarity", 5), 1, 10, 5),
                honesty=_clamp(soft_data.get("honesty", 5), 1, 10, 5),
                engagement=_clamp(soft_data.get("engagement", 5), 1, 10, 5),
                problem_solving=_clamp(soft_data.get("problem_solving", 5), 1, 10, 5),
                communication_style=soft_data.get("communication_style", ""),
                red_flags=soft_data.get("red_flags", []),
            )

            roadmap = [
                RoadmapItem(
                    topic=item.get("topic", ""),
                    priority=item.get("priority", "medium"),
                    resources=item.get("resources", []),
                )
                for item in data.get("roadmap", [])
            ]

            return FinalFeedback(
                decision=decision,
                behavior=behavior,
                hard_skills=hard_skills,
                soft_skills=soft_skills,
                roadmap=roadmap,
                interview_summary=data.get("interview_summary", ""),
                total_turns=len(state.get("turns", [])),
            )

        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
            return self._fallback_feedback(state, str(e))

    def _fallback_feedback(self, state: InterviewState, error: str) -> FinalFeedback:
        """Создать fallback-фидбэк при ошибке парсинга."""
        return FinalFeedback(
            decision=Decision(
                assessed_grade=state.get("grade", "Junior"),
                target_grade=state.get("grade", ""),
                hiring_recommendation="No Hire",
                confidence_score=30,
                grade_match="match",
                summary=f"Ошибка генерации: {error}",
            ),
            behavior=BehaviorAnalysis(
                evasion_count=state.get("evasion_count", 0),
                hallucination_count=state.get("hallucination_count", 0),
                confident_nonsense_count=state.get("confident_nonsense_count", 0),
                hints_used=state.get("hints_used", 0),
                notes=["Автоматический анализ поведения недоступен."],
            ),
            hard_skills=HardSkillsAnalysis(
                confirmed_skills=list(state.get("covered_topics", [])),
                knowledge_gaps=[],
                technical_depth=5,
                notes="Автоматическая оценка недоступна.",
            ),
            soft_skills=SoftSkillsAnalysis(
                clarity=5, honesty=5, engagement=5, problem_solving=5,
                communication_style="Недостаточно данных.",
                red_flags=[],
            ),
            roadmap=[],
            interview_summary="Интервью завершено, но автоматическая оценка не удалась.",
            total_turns=len(state.get("turns", [])),
        )
