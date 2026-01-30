"""LangGraph workflow для оркестрации интервью."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph

from src.agents.evaluator import EvaluatorAgent
from src.agents.interviewer import InterviewerAgent
from src.agents.observer import ObserverAgent
from src.config import settings
from src.llm.provider import get_llm_for_agent
from src.models.state import InterviewState, SoftSkillsTracker, Turn


def create_interview_graph() -> StateGraph:
    """Создать и скомпилировать граф workflow интервью."""
    interviewer = InterviewerAgent(get_llm_for_agent("interviewer"))
    observer = ObserverAgent(get_llm_for_agent("observer"))
    evaluator = EvaluatorAgent(get_llm_for_agent("evaluator"))

    graph = StateGraph(InterviewState)

    def interviewer_node(state: InterviewState) -> dict:
        return interviewer.process_sync(state)

    def observer_node(state: InterviewState) -> dict:
        return observer.process_sync(state)

    def evaluator_node(state: InterviewState) -> dict:
        return evaluator.process_sync(state)

    def save_turn_node(state: InterviewState) -> dict:
        turn_id = state.get("current_turn_id", 0) + 1
        thoughts = "\n".join(s for s in state.get("internal_thoughts_buffer", []) if s.strip())

        turn = Turn(
            turn_id=turn_id,
            agent_visible_message=state.get("current_agent_message", ""),
            user_message=state.get("current_user_message", ""),
            internal_thoughts=thoughts,
        )

        return {
            "turns": [turn],
            "current_turn_id": turn_id,
            "internal_thoughts_buffer": [],
        }

    def check_termination(state: InterviewState) -> Literal["continue", "finish"]:
        if state.get("is_finished", False):
            return "finish"
        analysis = state.get("current_observer_analysis")
        if analysis and getattr(analysis, "wants_to_end_interview", False):
            return "finish"
        if state.get("current_turn_id", 0) >= settings.max_turns:
            return "finish"
        return "continue"

    graph.add_node("interviewer", interviewer_node)
    graph.add_node("observer", observer_node)
    graph.add_node("save_turn", save_turn_node)
    graph.add_node("evaluator", evaluator_node)

    graph.set_entry_point("interviewer")
    graph.add_edge("interviewer", "observer")
    graph.add_edge("observer", "save_turn")
    graph.add_conditional_edges(
        "save_turn",
        check_termination,
        {"continue": "interviewer", "finish": "evaluator"},
    )
    graph.add_edge("evaluator", END)

    return graph.compile()


class InterviewSession:
    """Управляет потоком интервью с кешированными агентами."""

    __slots__ = ("_state", "_interviewer", "_observer", "_evaluator", "_initialized")

    def __init__(self):
        self._state: InterviewState | None = None
        self._interviewer: InterviewerAgent | None = None
        self._observer: ObserverAgent | None = None
        self._evaluator: EvaluatorAgent | None = None
        self._initialized = False

    @property
    def _cached_interviewer(self) -> InterviewerAgent:
        if self._interviewer is None:
            self._interviewer = InterviewerAgent(get_llm_for_agent("interviewer"))
        return self._interviewer

    @property
    def _cached_observer(self) -> ObserverAgent:
        if self._observer is None:
            self._observer = ObserverAgent(get_llm_for_agent("observer"))
        return self._observer

    @property
    def _cached_evaluator(self) -> EvaluatorAgent:
        if self._evaluator is None:
            self._evaluator = EvaluatorAgent(get_llm_for_agent("evaluator"))
        return self._evaluator

    def initialize(
        self,
        participant_name: str,
        position: str,
        grade: str,
        experience: str,
    ) -> str:
        """Начать новую сессию интервью, вернуть приветствие."""
        initial_difficulty = self._get_initial_difficulty(grade)
        
        self._state = InterviewState(
            participant_name=participant_name,
            position=position,
            grade=grade,
            experience=experience,
            turns=[],
            current_turn_id=0,
            current_difficulty=initial_difficulty,
            covered_topics=[],
            skipped_topics=[],
            skill_scores={},
            candidate_mentioned=[],
            interview_phase="intro",
            technical_questions_count=0,
            evasion_count=0,
            hallucination_count=0,
            confident_nonsense_count=0,
            spam_count=0,
            overqualified_signals=0,
            underqualified_signals=0,
            hints_used=0,
            soft_skills_tracker=SoftSkillsTracker(),
            current_user_message="",
            current_agent_message="",
            current_observer_analysis=None,
            internal_thoughts_buffer=[],
            is_finished=False,
            finish_reason="",
            final_feedback=None,
        )

        result = self._cached_interviewer.process_sync(self._state)
        self._state["current_agent_message"] = result.get("current_agent_message", "")
        self._state["internal_thoughts_buffer"] = result.get("internal_thoughts_buffer", [])
        self._initialized = True

        return self._state["current_agent_message"]

    def _get_initial_difficulty(self, grade: str) -> int:
        """Установить начальную сложность вопросов на основе грейда."""
        grade_lower = grade.lower()
        if "senior" in grade_lower:
            return 3
        if "middle" in grade_lower:
            return 2
        return 1

    def process_user_input(self, user_message: str) -> tuple[str, bool, dict | None]:
        """Обработать ввод пользователя, вернуть (ответ, завершено, фидбэк)."""
        if not self._initialized or self._state is None:
            raise RuntimeError("Session not initialized. Call initialize() first.")

        self._state["current_user_message"] = user_message

        if self._state.get("interview_phase") == "intro":
            self._state["interview_phase"] = "technical"

        observer_result = self._cached_observer.process_sync(self._state)
        for key, value in observer_result.items():
            if key == "internal_thoughts_buffer":
                self._state["internal_thoughts_buffer"] = (
                    self._state.get("internal_thoughts_buffer", []) + value
                )
            elif key == "soft_skills_tracker" and value is not None:
                self._state["soft_skills_tracker"] = value
            else:
                self._state[key] = value

        self._save_current_turn(user_message)
        turn_count = self._state.get("current_turn_id", 0)
        self._state["technical_questions_count"] = turn_count

        if self._should_finish():
            return self._finish_interview()
        result = self._cached_interviewer.process_sync(self._state)
        self._state["current_agent_message"] = result.get("current_agent_message", "")
        self._state["internal_thoughts_buffer"] = result.get("internal_thoughts_buffer", [])

        return (self._state["current_agent_message"], False, None)

    def _save_current_turn(self, user_message: str) -> None:
        turn_id = self._state.get("current_turn_id", 0) + 1
        thoughts = "\n".join(s for s in self._state.get("internal_thoughts_buffer", []) if s.strip())

        turn = Turn(
            turn_id=turn_id,
            agent_visible_message=self._state.get("current_agent_message", ""),
            user_message=user_message,
            internal_thoughts=thoughts,
        )

        turns = list(self._state.get("turns", []))
        turns.append(turn)
        self._state["turns"] = turns
        self._state["current_turn_id"] = turn_id
        self._state["internal_thoughts_buffer"] = []

    def _should_finish(self) -> bool:
        """Проверить, должно ли интервью завершиться."""
        analysis = self._state.get("current_observer_analysis")
        if analysis and analysis.wants_to_end_interview:
            return True
        
        spam_count = self._state.get("spam_count", 0)
        evasion_count = self._state.get("evasion_count", 0)
        if spam_count >= settings.max_spam_count or evasion_count >= settings.max_evasion_count:
            return True
        
        return self._state.get("current_turn_id", 0) >= settings.max_turns

    def _finish_interview(self) -> tuple[str, bool, dict | None]:
        eval_result = self._cached_evaluator.process_sync(self._state)
        self._state["final_feedback"] = eval_result.get("final_feedback")
        self._state["is_finished"] = True
        self._state["finish_reason"] = eval_result.get("finish_reason", "user_stop")

        return ("Спасибо за интервью! Вот ваш фидбэк:", True, self._state["final_feedback"])

    def get_state(self) -> InterviewState | None:
        return self._state

    def get_turns(self) -> list[Turn]:
        return list(self._state.get("turns", [])) if self._state else []

    def is_finished(self) -> bool:
        return self._state.get("is_finished", False) if self._state else False

    def get_final_feedback(self) -> dict | None:
        return self._state.get("final_feedback") if self._state else None
