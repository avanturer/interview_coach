"""Агенты системы."""

from src.agents.base import BaseAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.interviewer import InterviewerAgent
from src.agents.observer import ObserverAgent

__all__ = [
    "BaseAgent",
    "InterviewerAgent",
    "ObserverAgent",
    "EvaluatorAgent",
]
