"""Shared constants."""

from typing import Final

CONTEXT_WINDOW_SIZE: Final[int] = 5
MIN_DIFFICULTY: Final[int] = 1
MAX_DIFFICULTY: Final[int] = 5

QUALITY_EXCELLENT: Final[int] = 8
QUALITY_GOOD: Final[int] = 7
QUALITY_POOR: Final[int] = 3

AGENT_INTERVIEWER: Final[str] = "interviewer"
AGENT_OBSERVER: Final[str] = "observer"
AGENT_EVALUATOR: Final[str] = "evaluator"
