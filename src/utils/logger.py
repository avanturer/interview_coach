"""JSON-логгер для сессий интервью в формате спецификации."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import settings
from src.models.feedback import (
    FinalFeedback,
    feedback_to_log_dict,
    feedback_to_submission_string,
)
from src.models.state import Turn


class InterviewLogger:
    """Логирует сессии интервью в JSON-формате по спецификации."""

    __slots__ = ("log_dir", "_log", "_file")

    def __init__(self, log_dir: Path | None = None):
        self.log_dir = log_dir or settings.log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log: dict[str, Any] = {}
        self._file: Path | None = None

    def start_session(self, participant_name: str, position: str, grade: str, experience: str) -> Path:
        """Инициализировать новую сессию, вернуть путь к файлу лога."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() else "_" for c in participant_name)
        self._file = self.log_dir / f"interview_{safe_name}_{ts}.json"

        self._log = {
            "format_version": "1.0",
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
        """Добавить ход в лог."""
        if not self._log:
            raise RuntimeError("Нет активной сессии")

        self._log["turns"].append({
            "turn_id": turn.turn_id,
            "agent_visible_message": turn.agent_visible_message,
            "user_message": turn.user_message,
            "internal_thoughts": turn.internal_thoughts,
        })
        self._save()

    def log_feedback(self, feedback: FinalFeedback | dict) -> None:
        """Записать финальный фидбэк."""
        if not self._log:
            raise RuntimeError("Нет активной сессии")

        self._log["final_feedback"] = (
            feedback_to_log_dict(feedback) if isinstance(feedback, FinalFeedback) else feedback
        )
        self._log["finished_at"] = datetime.now().isoformat()
        self._save()

    def end_session(self, feedback: FinalFeedback | dict | None = None) -> Path:
        """Завершить сессию и вернуть путь к логу."""
        if not self._log:
            raise RuntimeError("Нет активной сессии")

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
    """Загрузить лог из JSON-файла."""
    return json.loads(path.read_text(encoding="utf-8"))


def export_for_submission(
    log_data: dict[str, Any],
    output_path: Path,
    feedback: FinalFeedback | dict | None = None,
) -> Path:
    """Экспорт в формат инструкции 1:1: participant_name, turns, final_feedback (строка)."""
    out = {
        "participant_name": log_data.get("participant_name", ""),
        "turns": [
            {
                "turn_id": t.get("turn_id"),
                "agent_visible_message": t.get("agent_visible_message", ""),
                "user_message": t.get("user_message", ""),
                "internal_thoughts": t.get("internal_thoughts", ""),
            }
            for t in log_data.get("turns", [])
        ],
        "final_feedback": "",
    }

    if feedback:
        if isinstance(feedback, FinalFeedback):
            out["final_feedback"] = feedback_to_submission_string(feedback)
        elif isinstance(feedback, dict):
            fb_obj = log_data.get("final_feedback", feedback)
            out["final_feedback"] = _dict_feedback_to_string(fb_obj)
    elif ff := log_data.get("final_feedback"):
        out["final_feedback"] = _dict_feedback_to_string(ff) if isinstance(ff, dict) else str(ff)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def _dict_feedback_to_string(fb: dict) -> str:
    """Конвертировать dict-фидбэк в строку."""
    d = fb.get("decision", {})
    h = fb.get("hard_skills", {})
    s = fb.get("soft_skills", {})
    parts = [
        f"Вердикт: {d.get('assessed_grade', d.get('grade', '?'))} | {d.get('hiring_recommendation', '?')} | {d.get('confidence_score', 0)}%",
        d.get("summary", ""),
        "",
        "Hard Skills:",
        f"Подтверждено: {', '.join(h.get('confirmed_skills', h.get('confirmed', [])) or []) or 'нет'}",
    ]
    for gap in h.get("knowledge_gaps", h.get("gaps", [])):
        ans = gap.get("correct_answer", "")[:200]
        if len(gap.get("correct_answer", "")) > 200:
            ans += "..."
        parts.append(f"- {gap.get('topic', '?')}: {ans}")
    parts.extend([
        "",
        f"Soft Skills: Ясность {s.get('clarity', '-')}/10 | Честность {s.get('honesty', '-')}/10",
        f"Roadmap: {', '.join(r.get('topic', '') for r in fb.get('roadmap', []))}",
        "",
        fb.get("interview_summary", ""),
    ])
    return "\n".join(parts).strip()
