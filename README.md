# Task Manager

Task Manager is a terminal application for creating and organising personal
tasks.

Tasks can have a priority and an optional due date. They are saved between
program executions and can be listed in priority or date order. The application
also prevents exact duplicates and allows saved tasks to be deleted.

## Getting started

### Requirements

The project requires:

- Git
- [uv](https://docs.astral.sh/uv/)
- Python 3.13 or newer

### Installation

Clone the repository:

```bash
git clone https://github.com/esade-swdev-2026/task-manager.git
cd task-manager
```

Install the project and its dependencies:

```bash
uv sync
```

Confirm that the command is available:

```bash
uv run task-manager --help
```

## Example workflow

The following commands create three tasks with different priorities and due
dates.

```bash
uv run task-manager add "Prepare finance presentation" --priority high --due-date 2026-10-20
uv run task-manager add "Book dentist appointment" --priority low --due-date 2026-10-17
uv run task-manager add "Buy printer paper"
```

The program confirms where each task has been saved:

```text
added Prepare finance presentation with high priority to storage_tasks/tasks.csv
added Book dentist appointment with low priority to storage_tasks/tasks.csv
added Buy printer paper with medium priority to storage_tasks/tasks.csv
```

### List by priority

The default order is `high`, `medium`, and then `low`:

```bash
uv run task-manager list
```

```text
1. Prepare finance presentation - high - due 2026-10-20
2. Buy printer paper - medium
3. Book dentist appointment - low - due 2026-10-17
```

The priority order can also be requested explicitly:

```bash
uv run task-manager list --sort-by priority
```

### List by due date

Use the following option to show the earliest due date first:

```bash
uv run task-manager list --sort-by date
```

```text
1. Book dentist appointment - low - due 2026-10-17
2. Prepare finance presentation - high - due 2026-10-20
3. Buy printer paper - medium
```

Tasks without a due date are placed at the end.

### Delete a task

Run the delete command:

```bash
uv run task-manager delete
```

The application displays the current tasks and asks for the number of the task
to delete. The CSV file is then updated with the remaining tasks.

## Command reference

| Command | Purpose | Inputs |
|---|---|---|
| `add` | Validates and saves a new task. | Required title; optional `--priority` and `--due-date`. |
| `list` | Displays every saved task. | Optional `--sort-by priority` or `--sort-by date`. |
| `delete` | Displays the tasks and deletes the selected number. | The task number is requested interactively. |

More information about any command is available through `--help`:

```bash
uv run task-manager add --help
uv run task-manager list --help
uv run task-manager delete --help
```

## Input rules

A title cannot be empty.

Valid priorities are:

```text
low
medium
high
```

For example, an unsupported priority:

```bash
uv run task-manager add "Invalid task" --priority urgent
```

produces:

```text
Priority must be one of: low, medium, high.
```

Due dates must use the ISO `YYYY-MM-DD` format:

```bash
uv run task-manager add "Submit report" --due-date 2026-10-18
```

The valid list ordering values are `priority` and `date`. For example:

```bash
uv run task-manager list --sort-by name
```

produces:

```text
Sort must be one of: priority, date.
```

Invalid input produces a clear error and a non-zero exit code instead of a
traceback.

## Duplicate tasks

An exact duplicate has the same title, priority, and due date as an existing
task.

The application rejects exact duplicates, but permits tasks with the same title
when their priority or due date is different.

## Data storage

The application stores tasks in:

```text
storage_tasks/tasks.csv
```

The directory and CSV file are created automatically when the first task is
added.

The CSV contains three fields:

```text
title,priority,due_date
```

The `storage_tasks/` directory is ignored by Git. Task data therefore remains
local and is not included in commits.

Commands should be run from the project directory so that they use the same
CSV file.

## Project design

The source code is organised under `src/task_manager/`:

```text
src/task_manager/
    __init__.py
    __main__.py
    cli.py
    formatting.py
    models.py
    storage.py
    tasks.py
    validation.py
```

Responsibilities are separated as follows:

- `models.py` defines the `Task` data model.
- `validation.py` validates and normalises titles, priorities, and dates.
- `tasks.py` contains the task-management computations.
- `formatting.py` converts task data into displayable lines.
- `storage.py` reads and writes the CSV file.
- `cli.py` connects the core logic to terminal input and output.
- `__main__.py` provides the Python module entry point.

This follows a functional core / imperative shell design. Task computations
work with plain data and return results. File access and terminal output remain
outside the functional core.

Tests follow the same separation:

```text
tests/
    test_cli.py
    test_formatting.py
    test_models.py
    test_storage.py
    test_tasks.py
    test_validation.py
```

Most tests exercise pure functions with normal Python data. Storage and
command-line behaviour are tested separately.

## Project checks

Run the checks used by GitHub Actions:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
```

To apply the formatter before checking it:

```bash
uv run ruff format .
```

Every check must pass before changes are merged or a release tag is created.

## Generative AI disclosure

ChatGPT and Codex (OpenAI) were used as support tools.

The existing task logic and tests from the earlier checkpoints were used as the starting point. ChatGPT was used to review this code, explain errors and suggest edge cases. The group manually entered and adapted the changes and reviewed the responsibility of each module.

For CSV persistence and duplicate detection, ChatGPT helped explain how tasks could be written to and read from storage_tasks/tasks.csv. It also suggested tests for saving multiple tasks, malformed CSV rows, exact duplicates, and persistence between CLI executions. The group reviewed the suggestions and tested the final behaviour locally.

For task deletion and the list --sort-by date option, ChatGPT helped turn the intended behaviour into draft code and test cases. 

The wording and organisation of this README were drafted with ChatGPT. This included the installation instructions, command examples, storage explanation, project structure, development checks, and this AI disclosure. 

Codex was used to review the complete project against the partial-submission rubric and to identify missing tests, outdated documentation, and release requirements. The group made the final decisions about which suggestions to include and remains responsible for understanding and explaining the submitted code.
