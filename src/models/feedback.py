"""Feedback models for final interview report."""

from typing import Literal

from pydantic import BaseModel, Field


class Decision(BaseModel):
    """Hiring decision with grade match analysis."""

    assessed_grade: str  # Junior/Middle/Senior
    target_grade: str = ""  # What candidate claimed
    hiring_recommendation: str  # Hire/No Hire/Strong Hire
    confidence_score: int = Field(ge=0, le=100)
    grade_match: Literal["match", "overqualified", "underqualified"] = "match"
    summary: str


class KnowledgeGap(BaseModel):
    """Knowledge gap with correct answer."""

    topic: str
    question_asked: str
    candidate_answer: str
    correct_answer: str
    severity: str = "medium"  # low/medium/high


class BehaviorAnalysis(BaseModel):
    """Analysis of candidate's behavior during interview."""
    
    evasion_count: int = 0  # Times avoided answering
    hallucination_count: int = 0  # False facts detected
    confident_nonsense_count: int = 0  # Sounded confident but wrong
    hints_used: int = 0  # Hints given by interviewer
    notes: list[str] = Field(default_factory=list)


class HardSkillsAnalysis(BaseModel):
    """Technical skills analysis."""

    confirmed_skills: list[str] = Field(default_factory=list)
    knowledge_gaps: list[KnowledgeGap] = Field(default_factory=list)
    technical_depth: int = Field(ge=1, le=10)
    notes: str = ""


class SoftSkillsAnalysis(BaseModel):
    """Soft skills analysis."""

    clarity: int = Field(ge=1, le=10)
    honesty: int = Field(ge=1, le=10)
    engagement: int = Field(ge=1, le=10)
    problem_solving: int = Field(default=5, ge=1, le=10)
    communication_style: str = ""
    red_flags: list[str] = Field(default_factory=list)


class RoadmapItem(BaseModel):
    """Learning roadmap item."""

    topic: str
    priority: str  # high/medium/low
    resources: list[str] = Field(default_factory=list)


class FinalFeedback(BaseModel):
    """Complete final feedback."""

    decision: Decision
    behavior: BehaviorAnalysis = Field(default_factory=BehaviorAnalysis)
    hard_skills: HardSkillsAnalysis
    soft_skills: SoftSkillsAnalysis
    roadmap: list[RoadmapItem] = Field(default_factory=list)
    interview_summary: str = ""
    total_turns: int = 0


def feedback_to_log_dict(feedback: FinalFeedback) -> dict:
    """Convert FinalFeedback to dictionary format for JSON log."""
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
