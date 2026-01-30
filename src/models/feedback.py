"""Модели финального фидбэка."""

from typing import Literal

from pydantic import BaseModel, Field


class Decision(BaseModel):
    """Решение о найме с анализом соответствия грейду."""

    assessed_grade: str
    target_grade: str = ""
    hiring_recommendation: str
    confidence_score: int = Field(ge=0, le=100)
    grade_match: Literal["match", "overqualified", "underqualified"] = "match"
    summary: str


class KnowledgeGap(BaseModel):
    """Пробел в знаниях с правильным ответом."""

    topic: str
    question_asked: str
    candidate_answer: str
    correct_answer: str
    severity: str = "medium"


class BehaviorAnalysis(BaseModel):
    """Анализ поведения кандидата."""

    evasion_count: int = 0
    hallucination_count: int = 0
    confident_nonsense_count: int = 0
    hints_used: int = 0
    notes: list[str] = Field(default_factory=list)


class HardSkillsAnalysis(BaseModel):
    """Анализ технических навыков."""

    confirmed_skills: list[str] = Field(default_factory=list)
    knowledge_gaps: list[KnowledgeGap] = Field(default_factory=list)
    technical_depth: int = Field(ge=1, le=10)
    notes: str = ""


class SoftSkillsAnalysis(BaseModel):
    """Анализ soft skills."""

    clarity: int = Field(ge=1, le=10)
    honesty: int = Field(ge=1, le=10)
    engagement: int = Field(ge=1, le=10)
    problem_solving: int = Field(default=5, ge=1, le=10)
    communication_style: str = ""
    red_flags: list[str] = Field(default_factory=list)


class RoadmapItem(BaseModel):
    """Элемент roadmap для обучения."""

    topic: str
    priority: str
    resources: list[str] = Field(default_factory=list)


class FinalFeedback(BaseModel):
    """Полный финальный фидбэк."""

    decision: Decision
    behavior: BehaviorAnalysis = Field(default_factory=BehaviorAnalysis)
    hard_skills: HardSkillsAnalysis
    soft_skills: SoftSkillsAnalysis
    roadmap: list[RoadmapItem] = Field(default_factory=list)
    interview_summary: str = ""
    total_turns: int = 0


def feedback_to_log_dict(feedback: FinalFeedback) -> dict:
    """Конвертировать FinalFeedback в словарь для JSON-лога."""
    return {
        "decision": {
            "grade": feedback.decision.assessed_grade,
            "target_grade": feedback.decision.target_grade,
            "hiring_recommendation": feedback.decision.hiring_recommendation,
            "confidence_score": feedback.decision.confidence_score,
            "grade_match": feedback.decision.grade_match,
            "summary": feedback.decision.summary,
        },
        "behavior": {
            "evasion_count": feedback.behavior.evasion_count,
            "hallucination_count": feedback.behavior.hallucination_count,
            "confident_nonsense_count": feedback.behavior.confident_nonsense_count,
            "hints_used": feedback.behavior.hints_used,
            "notes": feedback.behavior.notes,
        },
        "hard_skills": {
            "confirmed": feedback.hard_skills.confirmed_skills,
            "gaps": [
                {
                    "topic": gap.topic,
                    "question": gap.question_asked,
                    "candidate_answer": gap.candidate_answer,
                    "correct_answer": gap.correct_answer,
                    "severity": gap.severity,
                }
                for gap in feedback.hard_skills.knowledge_gaps
            ],
            "technical_depth": feedback.hard_skills.technical_depth,
            "notes": feedback.hard_skills.notes,
        },
        "soft_skills": {
            "clarity": feedback.soft_skills.clarity,
            "honesty": feedback.soft_skills.honesty,
            "engagement": feedback.soft_skills.engagement,
            "problem_solving": feedback.soft_skills.problem_solving,
            "communication_style": feedback.soft_skills.communication_style,
            "red_flags": feedback.soft_skills.red_flags,
        },
        "roadmap": [
            {
                "topic": item.topic,
                "priority": item.priority,
                "resources": item.resources,
            }
            for item in feedback.roadmap
        ],
        "interview_summary": feedback.interview_summary,
        "total_turns": feedback.total_turns,
    }


def feedback_to_submission_string(feedback: FinalFeedback) -> str:
    """Конвертировать фидбэк в строку для формата сдачи (инструкция 1:1)."""
    d = feedback.decision
    b = feedback.behavior
    h = feedback.hard_skills
    s = feedback.soft_skills

    parts = [
        f"Вердикт: {d.assessed_grade} | {d.hiring_recommendation} | Уверенность: {d.confidence_score}%",
        d.summary,
        "",
        "Hard Skills:",
        f"Подтверждено: {', '.join(h.confirmed_skills) or 'нет'}",
    ]
    for gap in h.knowledge_gaps:
        ans = gap.correct_answer[:200] + "..." if len(gap.correct_answer) > 200 else gap.correct_answer
        parts.append(f"- {gap.topic}: правильный ответ — {ans}")
    parts.extend([
        "",
        f"Soft Skills: Ясность {s.clarity}/10 | Честность {s.honesty}/10 | Вовлечённость {s.engagement}/10",
        f"Roadmap: {', '.join(r.topic for r in feedback.roadmap)}",
        "",
        feedback.interview_summary or "",
    ])
    return "\n".join(parts).strip()
