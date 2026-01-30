"""JSON logger for interview sessions - matches specification format."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import settings
from src.models.feedback import FinalFeedback, feedback_to_log_dict
from src.models.state import Turn


class InterviewLogger:
    """Logs interview sessions to JSON format per specification."""

    __slots__ = ("log_dir", "_log", "_file")

    def __init__(self, log_dir: Path | None = None):
        self.log_dir = log_dir or settings.log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log: dict[str, Any] = {}
        self._file: Path | None = None

    def start_session(self, participant_name: str, position: str, grade: str, experience: str) -> Path:
        """Initialize new session, return log file path."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() else "_" for c in participant_name)
        self._file = self.log_dir / f"interview_{safe_name}_{ts}.json"

        self._log = {
            "participant_name": participant_name,
            "position": position,
            "grade": grade,
            "experience": experience,
            "started_at": datetime.now().isoformat(),
            "turns": [],
            "final_feedback": None,
        }
        self._save()
        return self._file

    def log_turn(self, turn: Turn) -> None:
        """Append turn to log."""
        if not self._log:
            raise RuntimeError("No active session")

        self._log["turns"].append({
            "turn_id": turn.turn_id,
            "agent_visible_message": turn.agent_visible_message,
            "user_message": turn.user_message,
            "internal_thoughts": turn.internal_thoughts,
        })
        self._save()

    def log_feedback(self, feedback: FinalFeedback | dict) -> None:
        """Set final feedback."""
        if not self._log:
            raise RuntimeError("No active session")

        self._log["final_feedback"] = (
            feedback_to_log_dict(feedback) if isinstance(feedback, FinalFeedback) else feedback
        )
        self._log["finished_at"] = datetime.now().isoformat()
        self._save()

    def end_session(self, feedback: FinalFeedback | dict | None = None) -> Path:
        """Finalize and return log path."""
        if not self._log:
            raise RuntimeError("No active session")

        if feedback:
            self.log_feedback(feedback)

        self._log["finished_at"] = datetime.now().isoformat()
        self._save()

        result = self._file
        self._log = {}
        self._file = None
        return result

    def get_current_log(self) -> dict[str, Any]:
        return self._log.copy()

    def _save(self) -> None:
        if self._file and self._log:
            self._file.write_text(json.dumps(self._log, ensure_ascii=False, indent=2), encoding="utf-8")


def load_interview_log(path: Path) -> dict[str, Any]:
    """Load log from JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))
