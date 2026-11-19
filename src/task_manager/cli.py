import csv
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from task_manager.edit_tasks import edit_task
from task_manager.formatting import format_calendar, format_weekly_review, view_tasks
from task_manager.models import Task
from task_manager.storage import append_task, read_tasks, write_tasks
from task_manager.tasks import (
    complete_task,
    count_tasks_by_priority,
    create_task,
    delete_task,
    filter_overdue_tasks,
    filter_tasks_by_priority,
    filter_tasks_by_status,
    get_original_task_number,
    is_duplicate,
    reopen_task,
    search_tasks,
    sort_tasks_by_due_date,
    sort_tasks_by_priority,
    task_summary,
    tasks_due_soon,
    tasks_for_today,
    weekly_review,
)

DATA_FILE = Path("storage_tasks") / "tasks.csv"

SORT_OPTIONS = ("priority", "date")

STATUS_OPTIONS = ("pending", "completed", "all", "overdue")

PRIORITY_FILTER_OPTIONS = ("high", "medium", "low", "all")

app = typer.Typer(help="A command-line tool for managing tasks.")


def current_date() -> date:
    return date.today()


def load_tasks_or_exit(path: Path) -> list[Task]:
    """Load tasks from CSV, returning an empty list if the file is missing."""
    try:
        return read_tasks(path)

    except FileNotFoundError:
        return []

    except (OSError, ValueError, csv.Error) as exc:
        typer.echo(f"could not read {path}: {exc}", err=True)
        raise typer.Exit(1) from None


def save_tasks_or_exit(path: Path, tasks: list[Task]) -> None:
    """Save tasks to CSV and handle writing errors."""
    try:
        write_tasks(path, tasks)
    except OSError:
        typer.echo(f"could not write {path}", err=True)
        raise typer.Exit(1) from None


def prompt_task_number(action: str) -> int:
    try:
        raw_number = typer.prompt(
            f"Task number to {action}",
            type=str,
            default="",
            show_default=False,
        )
    except (KeyboardInterrupt, EOFError):
        typer.echo("Task selection cancelled.", err=True)
        raise typer.Exit(1) from None

    try:
        return int(raw_number.strip())
    except ValueError:
        typer.echo("Invalid task number.", err=True)
        raise typer.Exit(1) from None


def select_task_number(
    tasks: list[Task],
    selectable_tasks: list[Task],
    action: str,
) -> int:
    """Display selectable tasks and return the original task number."""
    displayed_tasks = sort_tasks_by_priority(selectable_tasks)

    for line in view_tasks(displayed_tasks, current_date()):
        typer.echo(line)

    task_number = prompt_task_number(action)

    try:
        return get_original_task_number(tasks, displayed_tasks, task_number)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None


@app.callback()
def main(
    ctx: typer.Context,
    data_file: Annotated[
        Path,
        typer.Option(
            "--data-file",
            help="Path to the CSV file used to store tasks.",
        ),
    ] = DATA_FILE,
) -> None:
    """Manage your tasks."""
    ctx.obj = data_file


def get_data_file(ctx: typer.Context) -> Path:
    data_file = ctx.obj
    assert isinstance(data_file, Path)
    return data_file


@app.command()
def add(
    ctx: typer.Context,
    title: str,
    priority: str = typer.Option(
        "medium",
        help="Task priority: low, medium, or high.",
    ),
    due_date: str = typer.Option(
        "",
        help="Due date in YYYY-MM-DD format.",
    ),
    repeat: str = typer.Option(
        "none",
        "--repeat",
        help="Repeat the task: none, daily, weekly, or monthly.",
    ),
    repeat_until: str = typer.Option(
        "",
        "--repeat-until",
        help="Last occurrence date in YYYY-MM-DD format. Required with --repeat.",
    ),
    category: str = typer.Option(
        "other",
        help="Task category.",
    ),
) -> None:
    data_file = get_data_file(ctx)

    try:
        task = create_task(
            title,
            priority,
            due_date,
            recurrence=repeat,
            repeat_until=repeat_until,
            category=category,
        )
        if task.recurrence != "none" and not task.repeat_until:
            raise ValueError("Recurring tasks require --repeat-until.")
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    existing_tasks = load_tasks_or_exit(data_file)

    if is_duplicate(task, existing_tasks):
        typer.echo("Task already exists.", err=True)
        raise typer.Exit(1)

    try:
        append_task(data_file, task)
    except OSError:
        typer.echo(f"could not write {data_file}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"added {task.title} with {task.priority} priority to {data_file}")


@app.command("list")
def list_tasks(
    ctx: typer.Context,
    sort_by: str = typer.Option(
        "priority",
        help="Sort tasks by priority or date.",
    ),
    status: str = typer.Option(
        "all",
        help="Show pending, completed, overdue, or all tasks.",
    ),
    priority: str = typer.Option(
        "all",
        help="Show tasks with high, medium, low, or all priorities.",
    ),
) -> None:
    data_file = get_data_file(ctx)
    normalized_sort = sort_by.strip().lower()

    if normalized_sort not in SORT_OPTIONS:
        allowed = ", ".join(SORT_OPTIONS)
        typer.echo(f"Sort must be one of: {allowed}.", err=True)
        raise typer.Exit(1)

    normalized_status = status.strip().lower()

    if normalized_status not in STATUS_OPTIONS:
        allowed = ", ".join(STATUS_OPTIONS)
        typer.echo(f"Status must be one of: {allowed}.", err=True)
        raise typer.Exit(1)

    normalized_priority = priority.strip().lower()

    if normalized_priority not in PRIORITY_FILTER_OPTIONS:
        allowed = ", ".join(PRIORITY_FILTER_OPTIONS)
        typer.echo(f"Priority filter must be one of: {allowed}.", err=True)
        raise typer.Exit(1)

    tasks = load_tasks_or_exit(data_file)

    if not tasks:
        typer.echo("No tasks found.")
        return

    today = current_date()

    if normalized_status == "overdue":
        tasks = filter_overdue_tasks(tasks, today)
    else:
        tasks = filter_tasks_by_status(tasks, normalized_status)

    if not tasks:
        typer.echo(f"No {normalized_status} tasks found.")
        return

    tasks = filter_tasks_by_priority(tasks, normalized_priority)

    if not tasks:
        typer.echo("No tasks match the selected filters.")
        return

    if normalized_sort == "date":
        tasks = sort_tasks_by_due_date(tasks)
    else:
        tasks = sort_tasks_by_priority(tasks)

    for line in view_tasks(tasks, today):
        typer.echo(line)


@app.command()
def today(ctx: typer.Context) -> None:
    """Show pending tasks that are overdue or due today."""
    data_file = get_data_file(ctx)
    tasks = load_tasks_or_exit(data_file)
    reference_date = current_date()

    selected_tasks = tasks_for_today(tasks, reference_date)

    if not selected_tasks:
        typer.echo("No tasks due today or overdue.")
        return

    for line in view_tasks(selected_tasks, reference_date, highlight_due_today=True):
        typer.echo(line)


@app.command("due-soon")
def due_soon(ctx: typer.Context) -> None:
    """Show pending tasks due within the next seven days."""
    data_file = get_data_file(ctx)
    tasks = load_tasks_or_exit(data_file)
    reference_date = current_date()

    selected_tasks = tasks_due_soon(tasks, reference_date)

    if not selected_tasks:
        typer.echo("No tasks due in the next seven days.")
        return

    for line in view_tasks(selected_tasks, reference_date):
        typer.echo(line)


@app.command()
def summary(ctx: typer.Context) -> None:
    """Show statistics about all tasks."""
    data_file = get_data_file(ctx)
    tasks = load_tasks_or_exit(data_file)
    statistics = task_summary(tasks, current_date())

    typer.echo("Task Summary")
    typer.echo("------------")
    typer.echo(f"Total tasks: {statistics['total']}")
    typer.echo(f"Pending: {statistics['pending']}")
    typer.echo(f"Completed: {statistics['completed']}")
    typer.echo(f"Overdue: {statistics['overdue']}")
    typer.echo(f"Completion rate: {statistics['completion_rate']:.1f}%")
    typer.echo("")
    typer.echo("Tasks by priority:")
    typer.echo(f"High: {statistics['high']}")
    typer.echo(f"Medium: {statistics['medium']}")
    typer.echo(f"Low: {statistics['low']}")


@app.command()
def delete(ctx: typer.Context) -> None:
    data_file = get_data_file(ctx)
    tasks = load_tasks_or_exit(data_file)

    if not tasks:
        typer.echo("No tasks found.", err=True)
        raise typer.Exit(1)

    original_task_number = select_task_number(tasks, tasks, "delete")

    try:
        deleted_task, remaining_tasks = delete_task(tasks, original_task_number)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    save_tasks_or_exit(data_file, remaining_tasks)

    typer.echo(f"deleted {deleted_task.title}")


@app.command()
def done(ctx: typer.Context) -> None:
    """Mark a pending task as completed."""
    data_file = get_data_file(ctx)
    tasks = load_tasks_or_exit(data_file)

    pending_tasks = [task for task in tasks if task.status == "pending"]

    if not pending_tasks:
        typer.echo("No pending tasks found.", err=True)
        raise typer.Exit(1)

    original_task_number = select_task_number(tasks, pending_tasks, "complete")

    try:
        completed_task, updated_tasks = complete_task(tasks, original_task_number, current_date())
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    save_tasks_or_exit(data_file, updated_tasks)

    typer.echo(f"completed {completed_task.title}")


@app.command()
def reopen(ctx: typer.Context) -> None:
    """Reopen a completed task."""
    data_file = get_data_file(ctx)
    tasks = load_tasks_or_exit(data_file)

    completed_tasks = [task for task in tasks if task.status == "completed"]

    if not completed_tasks:
        typer.echo("No completed tasks found.", err=True)
        raise typer.Exit(1)

    original_task_number = select_task_number(tasks, completed_tasks, "reopen")

    try:
        reopened_task, updated_tasks = reopen_task(tasks, original_task_number)

    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    save_tasks_or_exit(data_file, updated_tasks)

    typer.echo(f"reopened {reopened_task.title}")


@app.command()
def priority(ctx: typer.Context) -> None:
    data_file = get_data_file(ctx)
    tasks = load_tasks_or_exit(data_file)

    counts = count_tasks_by_priority(tasks)

    typer.echo("Tasks by priority:")
    for priority_level in ("high", "medium", "low"):
        typer.echo(f"{priority_level.capitalize()}: {counts[priority_level]}")

    if not tasks:
        typer.echo("No tasks found.")
        return

    sorted_tasks = sort_tasks_by_priority(tasks)

    typer.echo("\nTasks sorted by priority:")

    for line in view_tasks(sorted_tasks, current_date()):
        typer.echo(line)


@app.command()
def search(ctx: typer.Context, keyword: str) -> None:
    """Search saved tasks by a keyword in their title."""
    normalized_keyword = keyword.strip()

    if not normalized_keyword:
        typer.echo("Search keyword cannot be empty.", err=True)
        raise typer.Exit(1)

    tasks = load_tasks_or_exit(get_data_file(ctx))
    if not tasks:
        typer.echo("No tasks found.")
        return

    matching_tasks = search_tasks(tasks, normalized_keyword)

    if not matching_tasks:
        typer.echo("No matching tasks found.")
        return

    for line in view_tasks(matching_tasks, current_date()):
        typer.echo(line)


@app.command()
def edit(
    ctx: typer.Context,
    title: str | None = typer.Option(None, help="New task title."),
    priority: str | None = typer.Option(None, help="New priority: low, medium, or high."),
    due_date: str | None = typer.Option(
        None,
        help="New due date in YYYY-MM-DD format. Use an empty string to clear it.",
    ),
    category: str | None = typer.Option(None, help="New task category."),
) -> None:
    """Edit a saved task selected by its displayed number."""
    data_file = get_data_file(ctx)

    if title is None and priority is None and due_date is None and category is None:
        typer.echo("Provide at least one field to edit.", err=True)
        raise typer.Exit(1)

    tasks = load_tasks_or_exit(data_file)

    if not tasks:
        typer.echo("No tasks found.", err=True)
        raise typer.Exit(1)

    original_task_number = select_task_number(tasks, tasks, "edit")

    try:
        edited_task, updated_tasks = edit_task(
            tasks,
            original_task_number,
            title=title,
            priority=priority,
            due_date=due_date,
            category=category,
        )
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    other_tasks = [
        task for index, task in enumerate(tasks, start=1) if index != original_task_number
    ]

    if is_duplicate(edited_task, other_tasks):
        typer.echo("Task already exists.", err=True)
        raise typer.Exit(1)

    save_tasks_or_exit(data_file, updated_tasks)

    typer.echo(f"edited {edited_task.title}")


@app.command("weekly-review")
def weekly_review_command(ctx: typer.Context) -> None:
    """Show a weekly overview of overdue, due-today, upcoming and completed tasks."""
    data_file = get_data_file(ctx)
    tasks = load_tasks_or_exit(data_file)
    reference_date = current_date()

    overdue_tasks, due_today_tasks, upcoming_tasks, completed_count = weekly_review(
        tasks, reference_date
    )

    report = format_weekly_review(
        overdue_tasks,
        due_today_tasks,
        upcoming_tasks,
        completed_count,
        reference_date,
    )

    for line in report:
        typer.echo(line)


@app.command()
def calendar(
    ctx: typer.Context,
    month: int | None = typer.Option(None, help="Month to display (1-12)."),
    year: int | None = typer.Option(None, help="Year to display."),
) -> None:
    """Display tasks in a monthly calendar."""
    today = current_date()

    selected_month = month if month is not None else today.month
    selected_year = year if year is not None else today.year

    if not 1 <= selected_month <= 12:
        typer.echo("Month must be between 1 and 12.", err=True)
        raise typer.Exit(1)

    if not 1 <= selected_year <= 9999:
        typer.echo("Year must be between 1 and 9999.", err=True)
        raise typer.Exit(1)

    tasks = load_tasks_or_exit(get_data_file(ctx))

    lines = format_calendar(tasks, selected_year, selected_month)

    for line in lines:
        typer.echo(line)


if __name__ == "__main__":
    app()
