import csv
from datetime import date
from pathlib import Path

import typer

from task_manager.edit_tasks import edit_task
from task_manager.formatting import view_tasks
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


@app.callback()
def main() -> None:
    """Manage your tasks."""


@app.command()
def add(
    title: str,
    priority: str = typer.Option(
        "medium",
        help="Task priority: low, medium, or high.",
    ),
    due_date: str = typer.Option(
        "",
        help="Due date in YYYY-MM-DD format.",
    ),
) -> None:
    try:
        task = create_task(title, priority, due_date)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    existing_tasks = load_tasks_or_exit(DATA_FILE)

    if is_duplicate(task, existing_tasks):
        typer.echo("Task already exists.", err=True)
        raise typer.Exit(1)

    try:
        append_task(DATA_FILE, task)
    except OSError:
        typer.echo(f"could not write {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"added {task.title} with {task.priority} priority to {DATA_FILE}")


@app.command("list")
def list_tasks(
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

    tasks = load_tasks_or_exit(DATA_FILE)

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
def delete() -> None:
    tasks = load_tasks_or_exit(DATA_FILE)

    if not tasks:
        typer.echo("No tasks found.", err=True)
        raise typer.Exit(1)

    displayed_tasks = sort_tasks_by_priority(tasks)
    for line in view_tasks(displayed_tasks, current_date()):
        typer.echo(line)

    task_number = prompt_task_number("delete")

    try:
        original_task_number = get_original_task_number(tasks, displayed_tasks, task_number)
        deleted_task, remaining_tasks = delete_task(tasks, original_task_number)

    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    # Save remaining tasks without changing their original order
    try:
        write_tasks(DATA_FILE, remaining_tasks)
    except OSError:
        typer.echo(f"could not write {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"deleted {deleted_task.title}")


@app.command()
def done() -> None:
    """Mark a pending task as completed."""
    tasks = load_tasks_or_exit(DATA_FILE)

    pending_tasks = [task for task in tasks if task.status == "pending"]

    if not pending_tasks:
        typer.echo("No pending tasks found.", err=True)
        raise typer.Exit(1)

    displayed_tasks = sort_tasks_by_priority(pending_tasks)

    for line in view_tasks(displayed_tasks, current_date()):
        typer.echo(line)

    task_number = prompt_task_number("complete")

    try:
        original_task_number = get_original_task_number(tasks, displayed_tasks, task_number)
        completed_task, updated_tasks = complete_task(tasks, original_task_number)

    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    try:
        write_tasks(DATA_FILE, updated_tasks)
    except OSError:
        typer.echo(f"could not write {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"completed {completed_task.title}")


@app.command()
def reopen() -> None:
    """Reopen a completed task."""
    tasks = load_tasks_or_exit(DATA_FILE)

    completed_tasks = [task for task in tasks if task.status == "completed"]

    if not completed_tasks:
        typer.echo("No completed tasks found.", err=True)
        raise typer.Exit(1)

    displayed_tasks = sort_tasks_by_priority(completed_tasks)

    for line in view_tasks(displayed_tasks, current_date()):
        typer.echo(line)

    task_number = prompt_task_number("reopen")

    try:
        original_task_number = get_original_task_number(tasks, displayed_tasks, task_number)
        reopened_task, updated_tasks = reopen_task(tasks, original_task_number)

    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    try:
        write_tasks(DATA_FILE, updated_tasks)
    except OSError:
        typer.echo(f"could not write {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"reopened {reopened_task.title}")


@app.command()
def priority() -> None:
    tasks = load_tasks_or_exit(DATA_FILE)

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
def search(keyword: str) -> None:
    """Search saved tasks by a keyword in their title."""
    normalized_keyword = keyword.strip()

    if not normalized_keyword:
        typer.echo("Search keyword cannot be empty.", err=True)
        raise typer.Exit(1)

    tasks = load_tasks_or_exit(DATA_FILE)
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
    title: str | None = typer.Option(None, help="New task title."),
    priority: str | None = typer.Option(None, help="New priority: low, medium, or high."),
    due_date: str | None = typer.Option(
        None,
        help="New due date in YYYY-MM-DD format. Use an empty string to clear it.",
    ),
) -> None:
    """Edit a saved task selected by its displayed number."""
    if title is None and priority is None and due_date is None:
        typer.echo("Provide at least one field to edit.", err=True)
        raise typer.Exit(1)

    tasks = load_tasks_or_exit(DATA_FILE)

    if not tasks:
        typer.echo("No tasks found.", err=True)
        raise typer.Exit(1)

    displayed_tasks = sort_tasks_by_priority(tasks)

    for line in view_tasks(displayed_tasks, current_date()):
        typer.echo(line)

    task_number = prompt_task_number("edit")

    try:
        original_task_number = get_original_task_number(tasks, displayed_tasks, task_number)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    try:
        edited_task, updated_tasks = edit_task(
            tasks,
            original_task_number,
            title=title,
            priority=priority,
            due_date=due_date,
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

    try:
        write_tasks(DATA_FILE, updated_tasks)
    except OSError:
        typer.echo(f"could not write {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"edited {edited_task.title}")


if __name__ == "__main__":
    app()
