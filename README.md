# Task Manager

A simple command-line tool for managing tasks. It allows users to add tasks, assign a priority, and view all current tasks.

## Install

Install the project and its dependencies with:

```bash
uv sync


## Run

```
uv run app --help
uv run app add "Study Finance"
uv run app add "Study Finance" --priority high
uv run app list

```

## Develop

```
uv run ruff check .          # lint
uv run ruff format .         # format (CI runs `--check` and fails on a diff)
uv run mypy src tests        # types
uv run pytest                # tests
```

These four commands are exactly what `.github/workflows/check.yml` runs on every push.
If they pass here, CI passes.

## Layout

```
src/task_manager/
    cli.py          the Typer command-line interface / imperative shell
    tasks.py        the functional core with Task and task logic
    __main__.py     starts the application

tests/
    test_cli.py     tests the CLI commands
    test_tasks.py   tests the functional core

pyproject.toml      dependencies and tool configuration

```
## I/O Shell

The project's I/O is located in `src/task_manager/cli.py`, where user-facing output is handled with `typer.echo`.

The task data and business logic are located in `src/task_manager/tasks.py`.