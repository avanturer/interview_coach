"""Промпты агентов."""

from src.prompts.evaluator import EVALUATOR_SYSTEM_PROMPT, get_evaluator_prompt
from src.prompts.interviewer import INTERVIEWER_SYSTEM_PROMPT, get_interviewer_prompt
from src.prompts.observer import OBSERVER_SYSTEM_PROMPT, get_observer_prompt

__all__ = [
    "INTERVIEWER_SYSTEM_PROMPT",
    "OBSERVER_SYSTEM_PROMPT",
    "EVALUATOR_SYSTEM_PROMPT",
    "get_interviewer_prompt",
    "get_observer_prompt",
    "get_evaluator_prompt",
]
