from pathlib import Path

import typer

from task_manager.formatting import view_tasks
from task_manager.models import Task
from task_manager.storage import (
    append_task,
    read_tasks,
    write_tasks,
)
from task_manager.tasks import (
    create_task,
    delete_task,
    is_duplicate,
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
        task = create_task(
            title,
            priority,
            due_date,
        )
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None

    existing_tasks: list[Task] = []

    if DATA_FILE.exists():
        try:
            existing_tasks = read_tasks(DATA_FILE)
        except (OSError, ValueError):
            typer.echo(
                f"could not read {DATA_FILE}",
                err=True,
            )
            raise typer.Exit(1) from None

    if is_duplicate(task, existing_tasks):
        typer.echo(
            "Task already exists.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        append_task(DATA_FILE, task)
    except OSError:
        typer.echo(
            f"could not write {DATA_FILE}",
            err=True,
        )
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
        typer.echo(
            f"Sort must be one of: {allowed}.",
            err=True,
        )
        raise typer.Exit(1)

    if not DATA_FILE.exists():
        typer.echo("No tasks found.")
        return

    try:
        tasks = read_tasks(DATA_FILE)
    except (OSError, ValueError):
        typer.echo(
            f"could not read {DATA_FILE}",
            err=True,
        )
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
        typer.echo(
            "No tasks found.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        tasks = read_tasks(DATA_FILE)
    except (OSError, ValueError):
        typer.echo(
            f"could not read {DATA_FILE}",
            err=True,
        )
        raise typer.Exit(1) from None

    tasks = sort_tasks_by_priority(tasks)

    if not tasks:
        typer.echo(
            "No tasks found.",
            err=True,
        )
        raise typer.Exit(1)

    for line in view_tasks(tasks):
        typer.echo(line)

    task_number = typer.prompt(
        "Task number to delete",
        type=int,
    )

    try:
        deleted_task, remaining_tasks = delete_task(tasks, task_number)
    except ValueError as error:
        typer.echo(
            str(error),
            err=True,
        )
        raise typer.Exit(1) from None

    try:
        write_tasks(
            DATA_FILE,
            remaining_tasks,
        )
    except OSError:
        typer.echo(
            f"could not write {DATA_FILE}",
            err=True,
        )
        raise typer.Exit(1) from None

    typer.echo(f"deleted {deleted_task.title}")


if __name__ == "__main__":
    app()
