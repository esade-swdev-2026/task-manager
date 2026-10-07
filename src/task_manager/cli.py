# Imperative shell:
import typer

from task_manager.tasks import Task, add_task

app = typer.Typer(help="A command-line tool for managing tasks.")
tasks: list[Task] = []

@app.callback()
def main() -> None:
    """Manage your tasks"""


@app.command()
def add(title: str, priority: str = "medium") -> None:
    task = add_task(tasks, title, priority)
    typer.echo(f"Added {task.title} with {task.priority} priority")

if __name__ == "__main__":
    app()
