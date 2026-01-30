"""CLI приложения Interview Coach."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.agents.base import LLMAPIError
from src.config import settings
from src.graph.interview_graph import InterviewSession
from src.topics import SUPPORTED_POSITIONS, normalize_position
from src.utils.logger import InterviewLogger, export_for_submission, load_interview_log

app = typer.Typer(name="interview-coach", add_completion=False)
console = Console(width=100)


def print_feedback(feedback: dict):
    """Вывести структурированный фидбэк."""
    console.print()
    console.print(Panel("[bold]ФИНАЛЬНЫЙ ФИДБЭК[/bold]", style="green"))

    decision = feedback.get("decision", {})
    table = Table(title="Вердикт", show_header=False, border_style="cyan", expand=False)
    table.add_column("Параметр", style="cyan", width=20)
    table.add_column("Значение", style="white", width=76)  # 100 - рамки - параметр

    rec = decision.get("hiring_recommendation", "N/A")
    rec_style = {"Strong Hire": "bold green", "Hire": "green", "No Hire": "red"}.get(rec, "white")
    
    grade_match = decision.get("grade_match", "match")
    match_style = {"match": "green", "overqualified": "yellow", "underqualified": "red"}.get(grade_match, "white")
    assessed = decision.get("assessed_grade", decision.get("grade", "N/A"))
    target = decision.get("target_grade", "")
    grade_display = f"{assessed}"
    if grade_match != "match" and target:
        grade_display += f" [{match_style}]({grade_match} vs {target})[/{match_style}]"

    table.add_row("Грейд", grade_display)
    table.add_row("Рекомендация", f"[{rec_style}]{rec}[/{rec_style}]")
    table.add_row("Уверенность", f"{decision.get('confidence_score', 0)}%")
    table.add_row("Резюме", decision.get("summary", "N/A"))
    console.print(table)

    behavior = feedback.get("behavior", {})
    if behavior:
        issues = []
        if behavior.get("hallucination_count", 0) > 0:
            issues.append(f"[red]галлюцинаций: {behavior['hallucination_count']}[/red]")
        if behavior.get("confident_nonsense_count", 0) > 0:
            issues.append(f"[red]уверенного бреда: {behavior['confident_nonsense_count']}[/red]")
        if behavior.get("evasion_count", 0) > 0:
            issues.append(f"[yellow]уклонений: {behavior['evasion_count']}[/yellow]")
        if behavior.get("hints_used", 0) > 0:
            issues.append(f"подсказок: {behavior['hints_used']}")
        
        if issues:
            console.print(f"\n[bold cyan]Поведение[/bold cyan]: {' | '.join(issues)}")

    hard = feedback.get("hard_skills", {})
    console.print("\n[bold cyan]Технические навыки[/bold cyan]")
    
    confirmed = hard.get("confirmed_skills", []) or hard.get("confirmed", [])
    if confirmed:
        console.print(f"  [green]✓[/green] {', '.join(confirmed)}")

    gaps = hard.get("knowledge_gaps", []) or hard.get("gaps", [])
    if gaps:
        console.print("  [red]✗[/red] Пробелы:")
        for gap in gaps:
            topic = gap.get("topic", "?")
            correct = gap.get("correct_answer", "")
            console.print(f"    • {topic}")
            if correct:
                console.print(f"      [dim]→ {correct[:80]}{'...' if len(correct) > 80 else ''}[/dim]")

    soft = feedback.get("soft_skills", {})
    console.print("\n[bold cyan]Soft Skills[/bold cyan]")
    console.print(f"  Ясность: {soft.get('clarity', '-')}/10  |  Честность: {soft.get('honesty', '-')}/10  |  Вовлечённость: {soft.get('engagement', '-')}/10  |  Problem Solving: {soft.get('problem_solving', '-')}/10")

    flags = soft.get("red_flags", [])
    if flags:
        console.print(f"  [red]Red flags: {', '.join(flags)}[/red]")

    roadmap = feedback.get("roadmap", [])
    if roadmap:
        console.print("\n[bold cyan]Roadmap[/bold cyan]")
        icons = {"high": "[red]●[/red]", "medium": "[yellow]●[/yellow]", "low": "[green]●[/green]"}
        for item in roadmap:
            p = item.get("priority", "medium")
            console.print(f"  {icons.get(p, '○')} {item.get('topic', '?')}")
            resources = item.get("resources", [])
            if resources:
                for r in resources[:2]:
                    console.print(f"      [dim]→ {r}[/dim]")

    if summary := feedback.get("interview_summary"):
        console.print(f"\n[dim]{summary}[/dim]")


@app.command()
def interview(
    name: str = typer.Option(None, "-n", "--name", help="Имя кандидата (персонаж сценария)"),
    position: str = typer.Option(None, "-p", "--position", help="Позиция"),
    grade: str = typer.Option(None, "-g", "--grade", help="Грейд"),
    experience: str = typer.Option(None, "-e", "--experience", help="Опыт"),
    participant: str = typer.Option(
        None, "--participant",
        help="Ваше ФИО для participant_name в JSON (для сдачи жюри)",
    ),
    export: str = typer.Option(
        None, "--export",
        help="Путь для сохранения лога в формате ТЗ (interview_log_1.json и т.д.)",
    ),
):
    """Запустить интервью."""
    console.print("\n[bold cyan]Interview Coach[/bold cyan]")
    console.print("[dim]Мультиагентная система для технических интервью[/dim]\n")

    if export and not participant:
        participant = Prompt.ask(
            "[yellow]Ваше ФИО для participant_name (для жюри)[/yellow]",
            default="",
        ).strip()
        if not participant:
            console.print("[red]Для --export нужно указать --participant \"Ваше ФИО\"[/red]")
            raise typer.Exit(1)

    name = name or Prompt.ask("[cyan]Имя кандидата[/cyan]")
    
    if not position:
        console.print(f"[dim]Позиции: {', '.join(SUPPORTED_POSITIONS)}[/dim]")
        position = Prompt.ask("[cyan]Позиция[/cyan]", default="Backend Developer")
    
    normalized = normalize_position(position)
    while not normalized:
        console.print(f"[yellow]'{position}' не поддерживается.[/yellow]")
        console.print(f"[dim]Доступные: {', '.join(SUPPORTED_POSITIONS)}[/dim]")
        position = Prompt.ask("[cyan]Позиция[/cyan]", default="Backend Developer")
        normalized = normalize_position(position)
    
    if normalized != position:
        console.print(f"[dim]Позиция: {normalized}[/dim]")
    position = normalized
    
    grade = grade or Prompt.ask(
        "[cyan]Грейд[/cyan]",
        choices=["Junior", "Middle", "Senior", "Lead", "Expert", "Lead / Expert"],
        default="Junior",
    )
    experience = experience or Prompt.ask("[cyan]Опыт[/cyan]")

    console.print("\n[dim]Инициализация...[/dim]")

    session = InterviewSession()
    logger = InterviewLogger()

    try:
        greeting = session.initialize(name, position, grade, experience)
        log_file = logger.start_session(name, position, grade, experience)

        console.print(f"[dim]Лог: {log_file}[/dim]\n")
        console.print(Panel(greeting, title="Интервьюер", border_style="blue"))

        turn_count = 0
        while turn_count < settings.max_turns:
            user_input = Prompt.ask("\n[green]Вы[/green]")
            if not user_input.strip():
                continue

            console.print("[dim]Обработка...[/dim]")
            try:
                response, is_finished, feedback = session.process_user_input(user_input)
            except LLMAPIError as e:
                console.print(f"[red]Ошибка API: {e}[/red]")
                console.print("[dim]Попробуйте позже или переключите LLM_PROVIDER на openai в .env[/dim]")
                continue

            if state := session.get_state():
                if turns := state.get("turns"):
                    logger.log_turn(turns[-1])

            turn_count += 1

            if is_finished:
                console.print(Panel(response, title="Интервьюер", border_style="blue"))
                if feedback:
                    logger.log_feedback(feedback)
                    print_feedback(feedback)
                break

            console.print(Panel(response, title="Интервьюер", border_style="blue"))

        else:
            console.print("\n[yellow]Лимит вопросов. Генерация фидбэка...[/yellow]")
            try:
                _, _, feedback = session.process_user_input("стоп")
                if feedback:
                    logger.log_feedback(feedback)
                    print_feedback(feedback)
            except LLMAPIError as e:
                console.print(f"[red]Ошибка API при генерации фидбэка: {e}[/red]")

        final_log = logger.end_session()
        console.print(f"\n[green]Интервью завершено![/green]")
        console.print(f"[dim]Лог: {final_log}[/dim]")

        if participant and export:
            target = Path(export)
            if not target.is_absolute():
                target = settings.log_dir / target
            log_data = load_interview_log(final_log)
            export_for_submission(
                log_data, target,
                participant_name=participant,
            )
            console.print(f"[bold green]Файл для сдачи (формат ТЗ): {target}[/bold green]")
            console.print(f"[dim]participant_name: {participant}[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Прервано.[/yellow]")
        logger.end_session()
        sys.exit(0)


@app.command()
def view_log(log_file: Path = typer.Argument(..., help="Путь к файлу лога")):
    """Просмотреть лог интервью."""
    if not log_file.exists():
        console.print(f"[red]Файл не найден: {log_file}[/red]")
        raise typer.Exit(1)

    log = load_interview_log(log_file)
    console.print(Panel(f"Лог: {log.get('participant_name', '?')} | {log.get('position', '?')}", style="cyan"))

    for turn in log.get("turns", []):
        console.print(f"\n[dim]─── Ход {turn['turn_id']} ───[/dim]")
        console.print(Panel(turn["agent_visible_message"], title="Интервьюер", border_style="blue"))
        console.print(Panel(turn["user_message"], title="Кандидат", border_style="green"))
        if thoughts := turn.get("internal_thoughts"):
            console.print(f"[dim]{thoughts}[/dim]")

    if feedback := log.get("final_feedback"):
        if isinstance(feedback, str):
            console.print(Panel(feedback, title="Финальный фидбэк", border_style="green"))
        else:
            print_feedback(feedback)


@app.command()
def list_logs():
    """Показать все логи."""
    if not settings.log_dir.exists() or not (files := list(settings.log_dir.glob("interview_*.json"))):
        console.print("[yellow]Нет логов.[/yellow]")
        return

    table = Table(title="Логи интервью")
    table.add_column("Файл", style="cyan")
    table.add_column("Дата", style="green")

    for f in sorted(files, reverse=True):
        parts = f.stem.split("_")
        date = f"{parts[-2]} {parts[-1]}" if len(parts) >= 3 else "?"
        table.add_row(f.name, date)

    console.print(table)


@app.command()
def config():
    """Показать конфигурацию."""
    table = Table(title="Конфигурация")
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение")

    table.add_row("LLM Provider", settings.llm_provider)
    table.add_row("Model", settings.llm_model)
    table.add_row("Max Turns", str(settings.max_turns))
    table.add_row("Mistral API", "[green]✓[/green]" if settings.mistral_api_key else "[red]✗[/red]")

    console.print(table)


if __name__ == "__main__":
    app()
