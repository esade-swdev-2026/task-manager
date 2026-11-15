from pathlib import Path

import typer

from task_manager.edit_tasks import edit_task
from task_manager.formatting import view_tasks
from task_manager.models import Task
from task_manager.storage import append_task, read_tasks, write_tasks
from task_manager.tasks import (
    count_tasks_by_priority,
    create_task,
    delete_task,
    is_duplicate,
    search_tasks,
    sort_tasks_by_due_date,
    sort_tasks_by_priority,
)

DATA_FILE = Path("storage_tasks") / "tasks.csv"

SORT_OPTIONS = ("priority", "date")

app = typer.Typer(help="A command-line tool for managing tasks.")


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

    existing_tasks: list[Task] = []

    if DATA_FILE.exists():
        try:
            existing_tasks = read_tasks(DATA_FILE)
        except (OSError, ValueError):
            typer.echo(f"could not read {DATA_FILE}", err=True)
            raise typer.Exit(1) from None

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
) -> None:
    normalized_sort = sort_by.strip().lower()

    if normalized_sort not in SORT_OPTIONS:
        allowed = ", ".join(SORT_OPTIONS)
        typer.echo(f"Sort must be one of: {allowed}.", err=True)
        raise typer.Exit(1)

    if not DATA_FILE.exists():
        typer.echo("No tasks found.")
        return

    try:
        tasks = read_tasks(DATA_FILE)
    except (OSError, ValueError):
        typer.echo(f"could not read {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    if normalized_sort == "date":
        tasks = sort_tasks_by_due_date(tasks)
    else:
        tasks = sort_tasks_by_priority(tasks)

    lines = view_tasks(tasks)

    if not lines:
        typer.echo("No tasks found.")
        return

    for line in lines:
        typer.echo(line)


@app.command()
def delete() -> None:
    if not DATA_FILE.exists():
        typer.echo("No tasks found.", err=True)
        raise typer.Exit(1)

    try:
        tasks = read_tasks(DATA_FILE)
    except (OSError, ValueError):
        typer.echo(f"could not read {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    # Sort tasks only for display, preserving their original CSV order
    displayed_tasks = sort_tasks_by_priority(tasks)

    if not tasks:
        typer.echo("No tasks found.", err=True)
        raise typer.Exit(1)

    for line in view_tasks(displayed_tasks):
        typer.echo(line)

    task_number = typer.prompt("Task number to delete", type=int)

    # Validate the selected number
    if task_number < 1 or task_number > len(displayed_tasks):
        typer.echo("Task number does not exist.", err=True)
        raise typer.Exit(1)

    # Identify the task selected from the displayed list
    selected_task = displayed_tasks[task_number - 1]

    # Find its position in the original CSV order
    original_task_number = next(
        index for index, task in enumerate(tasks, start=1) if task is selected_task
    )

    # Delete the task from the original list
    try:
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
def priority() -> None:
    if not DATA_FILE.exists():
        typer.echo("No tasks found.")
        return

    try:
        tasks = read_tasks(DATA_FILE)
    except (OSError, ValueError):
        typer.echo(f"could not read {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    counts = count_tasks_by_priority(tasks)

    typer.echo("Tasks by priority:")
    for priority_level in ("high", "medium", "low"):
        typer.echo(f"{priority_level.capitalize()}: {counts[priority_level]}")

    if not tasks:
        typer.echo("No tasks found.")
        return

    sorted_tasks = sort_tasks_by_priority(tasks)

    typer.echo("\nTasks sorted by priority:")

    for line in view_tasks(sorted_tasks):
        typer.echo(line)


@app.command()
def search(keyword: str) -> None:
    """Search saved tasks by a keyword in their title."""
    normalized_keyword = keyword.strip()

    if not normalized_keyword:
        typer.echo("Search keyword cannot be empty.", err=True)
        raise typer.Exit(1)

    if not DATA_FILE.exists():
        typer.echo("No tasks found.")
        return

    try:
        tasks = read_tasks(DATA_FILE)
    except (OSError, ValueError):
        typer.echo(f"could not read {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    matching_tasks = search_tasks(tasks, normalized_keyword)

    if not matching_tasks:
        typer.echo("No matching tasks found.")
        return

    for line in view_tasks(matching_tasks):
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

    if not DATA_FILE.exists():
        typer.echo("No tasks found.", err=True)
        raise typer.Exit(1)

    try:
        tasks = read_tasks(DATA_FILE)
    except (OSError, ValueError):
        typer.echo(f"could not read {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    displayed_tasks = sort_tasks_by_priority(tasks)

    if not tasks:
        typer.echo("No tasks found.", err=True)
        raise typer.Exit(1)

    for line in view_tasks(displayed_tasks):
        typer.echo(line)

    raw_number = typer.prompt("Task number to edit", type=str)

    try:
        task_number = int(raw_number)
    except ValueError:
        typer.echo("Invalid task number.", err=True)
        raise typer.Exit(1) from None

    if task_number < 1 or task_number > len(displayed_tasks):
        typer.echo("Task number does not exist.", err=True)
        raise typer.Exit(1)

    selected_task = displayed_tasks[task_number - 1]
    task_number = next(index for index, task in enumerate(tasks, start=1) if task is selected_task)

    try:
        edited_task, updated_tasks = edit_task(
            tasks,
            task_number,
            title=title,
            priority=priority,
            due_date=due_date,
        )
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    other_tasks = [task for index, task in enumerate(tasks, start=1) if index != task_number]

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
