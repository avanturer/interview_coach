"""Модели состояния интервью."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class SkillScore(BaseModel):
    """Оценка навыка."""

    topic: str
    score: int = Field(default=0, ge=0, le=10)
    correct_answers: int = Field(default=0, ge=0)
    incorrect_answers: int = Field(default=0, ge=0)
    notes: list[str] = Field(default_factory=list)


class SoftSkillsTracker(BaseModel):
    """Трекер soft skills по ходу интервью."""

    clarity_scores: list[int] = Field(default_factory=list)
    honesty_signals: list[str] = Field(default_factory=list)
    engagement_signals: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)

    @property
    def avg_clarity(self) -> float:
        return sum(self.clarity_scores) / len(self.clarity_scores) if self.clarity_scores else 5.0


class Turn(BaseModel):
    """Один ход диалога."""

    turn_id: int
    agent_visible_message: str
    user_message: str
    internal_thoughts: str = ""


class ObserverAnalysis(BaseModel):
    """Анализ ответа кандидата от Observer."""

    wants_to_end_interview: bool = False
    wants_to_skip: bool = False
    topic_covered: bool = False

    current_topic: str = ""

    is_evasive: bool = False
    is_confident_nonsense: bool = False
    grade_mismatch: Literal["none", "overqualified", "underqualified"] = "none"
    is_spam_or_troll: bool = False

    is_valid_answer: bool = True
    is_hallucination: bool = False
    is_off_topic: bool = False
    is_question_from_user: bool = False
    user_question: str = ""
    answer_quality: int = Field(default=5, ge=1, le=10)
    detected_skills: list[str] = Field(default_factory=list)
    instruction_to_interviewer: str = ""
    thoughts: str = ""

    clarity_score: int = Field(default=5, ge=1, le=10)
    showed_honesty: bool = False
    showed_engagement: bool = False
    mentioned_info: list[str] = Field(default_factory=list)  # что кандидат упомянул о себе


class InterviewState(TypedDict, total=False):
    """Состояние интервью для LangGraph."""

    participant_name: str
    position: str
    grade: str
    experience: str

    turns: Annotated[list[Turn], "append"]
    current_turn_id: int
    current_difficulty: int
    covered_topics: list[str]
    skipped_topics: list[str]
    skill_scores: dict[str, SkillScore]
    candidate_mentioned: list[str]  # что кандидат рассказал о себе

    interview_phase: str
    technical_questions_count: int

    evasion_count: int
    hallucination_count: int
    confident_nonsense_count: int
    spam_count: int
    overqualified_signals: int
    underqualified_signals: int
    hints_used: int

    soft_skills_tracker: SoftSkillsTracker | None

    current_user_message: str
    current_agent_message: str
    current_observer_analysis: ObserverAnalysis | None
    internal_thoughts_buffer: list[str]

    is_finished: bool
    finish_reason: str
    final_feedback: dict | None


class InterviewInput(BaseModel):
    """Входные данные для начала интервью."""

    participant_name: str
    position: str
    grade: str
    experience: str


def create_initial_state(input_data: InterviewInput) -> InterviewState:
    """Создать начальное состояние интервью."""
    return InterviewState(
        participant_name=input_data.participant_name,
        position=input_data.position,
        grade=input_data.grade,
        experience=input_data.experience,
        turns=[],
        current_turn_id=0,
        current_difficulty=1,
        covered_topics=[],
        skill_scores={},
        current_user_message="",
        current_agent_message="",
        current_observer_analysis=None,
        internal_thoughts_buffer=[],
        is_finished=False,
        finish_reason="",
        final_feedback=None,
    )
