# Imperative shell:
import typer

from task_manager.tasks import Task, add_task, view_tasks

app = typer.Typer(help="A command-line tool for managing tasks.")
tasks: list[Task] = []


@app.callback()
def main() -> None:
    """Manage your tasks"""


@app.command()
def add(title: str, priority: str = "medium") -> None:
    task = add_task(tasks, title, priority)
    typer.echo(f"Added {task.title} with {task.priority} priority")


@app.command("list")
def list_tasks() -> None:
    lines = view_tasks(tasks)

    if not lines:
        typer.echo("No tasks found.")
        return

    for line in lines:
        typer.echo(line)


if __name__ == "__main__":
    app()
