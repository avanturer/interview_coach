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

import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.constants import VERSION
from src.graph.interview_graph import InterviewSession
from src.topics import SUPPORTED_POSITIONS, normalize_position
from src.utils.logger import InterviewLogger

console = Console()


def run_scenario(
    messages: list[str],
    name: str = "Тест",
    position: str = "Backend Developer",
    grade: str = "Junior",
    experience: str = "Python, SQL",
    output_name: str | None = None,
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
    
    greeting = session.initialize(name, position, grade, experience)
    log_file = logger.start_session(name, position, grade, experience)
    
    console.print(Panel(greeting, title="Интервьюер", border_style="blue"))
    
    # Process each message
    for i, msg in enumerate(messages, 1):
        console.print(f"\n[green]Кандидат ({i}/{len(messages)}):[/green] {msg}")
        
        response, is_finished, feedback = session.process_user_input(msg)
        
        # Log turn
        if state := session.get_state():
            if turns := state.get("turns"):
                logger.log_turn(turns[-1])
        
        console.print(Panel(response, title="Интервьюер", border_style="blue"))
        
        if is_finished and feedback:
            logger.log_feedback(feedback)
            console.print("\n[bold green]Фидбэк получен![/bold green]")
            _print_feedback_summary(feedback)
            break
    
    final_log = logger.end_session()

    if output_name:
        target = Path(output_name)
        if not target.is_absolute():
            target = Path("logs") / target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(final_log, target)
        console.print(f"\n[bold]Лог: {final_log}[/bold]")
        console.print(f"[bold]Копия для сдачи: {target}[/bold]")
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


def main():
    # Check API key
    if not settings.mistral_api_key:
        console.print("[red]Ошибка: MISTRAL_API_KEY не настроен в .env[/red]")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        scenario_file = Path(sys.argv[1])
        if not scenario_file.exists():
            console.print(f"[red]Файл не найден: {scenario_file}[/red]")
            sys.exit(1)

        metadata, messages = load_scenario(scenario_file)
        if not messages:
            console.print("[red]Сценарий пустой[/red]")
            sys.exit(1)

        output_name = sys.argv[2] if len(sys.argv) > 2 else None
        run_scenario(
            messages,
            name=metadata["name"],
            position=metadata["position"],
            grade=metadata["grade"],
            experience=metadata["experience"],
            output_name=output_name,
        )
    else:
        # Interactive mode
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
                    
                    # Check for stop signals
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
