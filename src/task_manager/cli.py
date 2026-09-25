import typer

app = typer.Typer(help="A command-line tool for managing tasks.")
tasks: list[dict[str, str]] = []

@app.callback()
def main() -> None:
    """Manage your tasks"""


@app.command()
def add(title: str,priority:str="medium") -> None:
    task = {"title": title, "priority": priority}
    tasks.append(task)
    typer.echo(f"Added {title} with {priority} priority")


if __name__ == "__main__":
    app()
