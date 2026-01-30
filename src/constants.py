"""Общие константы системы."""

from typing import Final

VERSION: Final[str] = "1.0.0"

MIN_DIFFICULTY: Final[int] = 1
MAX_DIFFICULTY: Final[int] = 5

QUALITY_EXCELLENT: Final[int] = 8
QUALITY_GOOD: Final[int] = 7
QUALITY_POOR: Final[int] = 3

AGENT_INTERVIEWER: Final[str] = "interviewer"
AGENT_OBSERVER: Final[str] = "observer"
AGENT_EVALUATOR: Final[str] = "evaluator"
