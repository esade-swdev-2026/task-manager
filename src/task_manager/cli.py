# Imperative shell:
import csv
from pathlib import Path

import typer

from task_manager.tasks import (
    create_task,
    read_tasks,
    sort_tasks_by_priority,
    view_tasks,
)

DATA_FILE = Path("data") / "tasks.csv"

app = typer.Typer(help="A command-line tool for managing tasks.")


@app.callback()
def main() -> None:
    """Manage your tasks"""


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

    DATA_FILE.parent.mkdir(exist_ok=True)
    is_new = not DATA_FILE.exists()

    with DATA_FILE.open("a", newline="") as handle:
        writer = csv.writer(handle)

        if is_new:
            writer.writerow(["title", "priority", "due_date"])

        writer.writerow([task.title, task.priority, task.due_date])

    print(f"added {task.title} with {task.priority} priority to {DATA_FILE}")


@app.command("list")
def list_tasks() -> None:
    if not DATA_FILE.exists():
        print("No tasks found.")
        return
    try:
        tasks = read_tasks(str(DATA_FILE))
    except (OSError, ValueError):
        typer.echo(f"could not read {DATA_FILE}", err=True)
        raise typer.Exit(1) from None

    tasks = sort_tasks_by_priority(tasks)
    lines = view_tasks(tasks)

    if not lines:
        print("No tasks found.")
        return

    for line in lines:
        print(line)


if __name__ == "__main__":
    app()
