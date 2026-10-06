# Task Manager

A simple command-line tool for managing tasks. It allows users to add tasks and assign a priority to each task.

## Install

Install the project and its dependencies with:

```bash
uv sync


## Run

```
uv run app --help
uv run app greet World
uv run app greet World --count 3
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
src/task_manager/          your package — importable, installable, not just a script
  cli.py          the typer command-line interface
  __main__.py     lets `python -m app` work
tests/            pytest tests, mirroring src/
pyproject.toml    dependencies and tool configuration — the single source of truth
```
## I/O Shell

The project's I/O is located in `src/task_manager/cli.py`, where user-facing output is handled with `typer.echo`.