#!/usr/bin/env python3
"""Скрипт для запуска сценариев интервью из файла или интерактивно.

Использование:
    python run_scenario.py scenario.txt  # Из файла
    python run_scenario.py               # Интерактивно

Формат файла сценария:
    name: Алекс
    position: Backend Developer
    grade: Junior
    experience: Python, SQL
    ---
    Привет, я Алекс, Junior Backend Developer
    Переменные в Python - это контейнеры для данных
    Стоп игра. Давай фидбэк
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base import LLMAPIError
from src.config import settings
from src.constants import VERSION
from src.graph.interview_graph import InterviewSession
from src.topics import SUPPORTED_POSITIONS, normalize_position
from src.main import print_feedback
from src.utils.logger import InterviewLogger, export_for_submission

console = Console(width=100)


def run_scenario(
    messages: list[str],
    name: str = "Тест",
    position: str = "Backend Developer",
    grade: str = "Junior",
    experience: str = "Python, SQL",
    output_name: str | None = None,
    participant_name_for_submission: str | None = None,
) -> Path:
    """Запустить сценарий и вернуть путь к файлу лога."""
    normalized = normalize_position(position)
    if not normalized:
        console.print(f"[red]Ошибка: '{position}' не поддерживается.[/red]")
        console.print(f"[dim]Доступные: {', '.join(SUPPORTED_POSITIONS)}[/dim]")
        sys.exit(1)
    position = normalized
    
    console.print(f"\n[bold cyan]Interview Coach v{VERSION}[/bold cyan]")
    console.print(f"[dim]Кандидат: {name} | Позиция: {position} | Грейд: {grade}[/dim]\n")
    
    session = InterviewSession()
    logger = InterviewLogger()
    
    try:
        greeting = session.initialize(name, position, grade, experience)
    except LLMAPIError as e:
        console.print(f"[red]Ошибка API при инициализации: {e}[/red]")
        console.print("[dim]Попробуйте позже или переключите LLM_PROVIDER на openai в .env[/dim]")
        sys.exit(1)
    log_file = logger.start_session(name, position, grade, experience)
    
    console.print(Panel(greeting, title="Интервьюер", border_style="blue"))
    
    for i, msg in enumerate(messages, 1):
        console.print(f"\n[green]Кандидат ({i}/{len(messages)}):[/green] {msg}")
        
        try:
            response, is_finished, feedback = session.process_user_input(msg)
        except LLMAPIError as e:
            console.print(f"[red]Ошибка API: {e}[/red]")
            console.print("[dim]Попробуйте позже или переключите LLM_PROVIDER на openai в .env[/dim]")
            sys.exit(1)
        
        if state := session.get_state():
            if turns := state.get("turns"):
                logger.log_turn(turns[-1])
        
        console.print(Panel(response, title="Интервьюер", border_style="blue"))
        
        if is_finished and feedback:
            logger.log_feedback(feedback)
            print_feedback(feedback)
            break

    final_log = logger.end_session()
    log_data = json.loads(final_log.read_text(encoding="utf-8"))
    last_feedback = feedback if (is_finished and feedback) else None

    if output_name:
        target = Path(output_name)
        if not target.is_absolute():
            target = Path("logs") / target
        export_for_submission(
            log_data, target, last_feedback,
            participant_name=participant_name_for_submission,
        )
        console.print(f"\n[bold]Лог: {final_log}[/bold]")
        console.print(f"[bold]Файл для сдачи (формат 1:1): {target}[/bold]")
        if participant_name_for_submission:
            console.print(f"[dim]participant_name в JSON: {participant_name_for_submission}[/dim]")
        return target

    console.print(f"\n[bold]Лог сохранён: {final_log}[/bold]")
    return final_log


def _print_feedback_summary(feedback: dict):
    """Вывести краткое резюме фидбэка."""
    decision = feedback.get("decision", {})
    console.print(f"  Грейд: {decision.get('assessed_grade', '?')}")
    console.print(f"  Рекомендация: {decision.get('hiring_recommendation', '?')}")
    console.print(f"  Уверенность: {decision.get('confidence_score', '?')}%")
    
    gaps = feedback.get("hard_skills", {}).get("knowledge_gaps", [])
    if gaps:
        console.print(f"  Пробелов: {len(gaps)}")


def load_scenario(file_path: Path) -> tuple[dict, list[str]]:
    """Загрузить сценарий из файла."""
    lines = file_path.read_text(encoding="utf-8").strip().split("\n")
    
    metadata = {
        "name": "Тест",
        "position": "Backend Developer",
        "grade": "Junior", 
        "experience": "Python",
    }
    messages = []
    in_messages = False
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        if line == "---":
            in_messages = True
            continue
        
        if in_messages:
            messages.append(line)
        else:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                if key in metadata:
                    metadata[key] = value
    
    return metadata, messages


def _parse_args():
    """Парсинг аргументов: scenario.txt [output.json] [--participant "ФИО"]."""
    argv = sys.argv[1:]
    participant = None
    skip_next = False
    pos_args = []
    for i, a in enumerate(argv):
        if skip_next:
            skip_next = False
            continue
        if a == "--participant" and i + 1 < len(argv):
            participant = argv[i + 1]
            skip_next = True
            continue
        pos_args.append(a)
    scenario_file = Path(pos_args[0]) if pos_args else None
    output_name = pos_args[1] if len(pos_args) > 1 else None
    return scenario_file, output_name, participant


def main():
    if not settings.mistral_api_key:
        console.print("[red]Ошибка: MISTRAL_API_KEY не настроен в .env[/red]")
        sys.exit(1)

    scenario_file, output_name, participant_for_submission = _parse_args()

    if scenario_file:
        if not scenario_file.exists():
            console.print(f"[red]Файл не найден: {scenario_file}[/red]")
            sys.exit(1)

        metadata, messages = load_scenario(scenario_file)
        if not messages:
            console.print("[red]Сценарий пустой[/red]")
            sys.exit(1)

        if output_name and not participant_for_submission:
            from rich.prompt import Prompt
            participant_for_submission = Prompt.ask(
                "[yellow]ФИО для participant_name в JSON (для жюри)[/yellow]",
                default="",
            ).strip()
            if not participant_for_submission:
                console.print("[yellow]participant_name будет из сценария. Для сдачи укажите --participant \"Ваше ФИО\"[/yellow]")

        run_scenario(
            messages,
            name=metadata["name"],
            position=metadata["position"],
            grade=metadata["grade"],
            experience=metadata["experience"],
            output_name=output_name,
            participant_name_for_submission=participant_for_submission or None,
        )
    else:
        console.print("[bold]Интерактивный режим[/bold]")
        console.print("[dim]Введите данные кандидата:[/dim]\n")
        
        from rich.prompt import Prompt
        
        name = Prompt.ask("Имя", default="Тест")
        position = Prompt.ask("Позиция", default="Backend Developer")
        grade = Prompt.ask("Грейд", choices=["Junior", "Middle", "Senior"], default="Junior")
        experience = Prompt.ask("Опыт", default="Python, SQL")
        
        console.print("\n[dim]Введите реплики (пустая строка = отправить, Ctrl+C = выход):[/dim]")
        
        messages = []
        try:
            while True:
                msg = Prompt.ask(f"\n[green]Реплика {len(messages)+1}[/green]")
                if msg.strip():
                    messages.append(msg)
                    
                    if any(s in msg.lower() for s in ["стоп", "stop", "фидбэк"]):
                        break
        except KeyboardInterrupt:
            pass
        
        if messages:
            run_scenario(messages, name, position, grade, experience)
        else:
            console.print("[yellow]Нет реплик[/yellow]")


if __name__ == "__main__":
    main()
