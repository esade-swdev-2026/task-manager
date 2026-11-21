# Task Manager

Task Manager is a terminal application for creating, organising, and tracking personal tasks.

Tasks can have a priority, an optional due date, a completion status, and a category. They are saved between program executions and can be listed, filtered, searched, edited, completed, reopened, or deleted.

The application also provides dedicated views for today's tasks and upcoming deadlines, as well as a summary of task statistics.


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
uv run task-manager add "Prepare finance presentation" --priority high --due-date 2027-10-20 --category university
uv run task-manager add "Book dentist appointment" --priority low --due-date 2027-10-17 --category personal
uv run task-manager add "Buy printer paper" --category personal

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
1. [PENDING] Prepare finance presentation - high - due 2027-10-20 - category university
2. [PENDING] Buy printer paper - medium - category personal
3. [PENDING] Book dentist appointment - low - due 2027-10-17 - category personal

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
1. [PENDING] Book dentist appointment - low - due 2027-10-17 - category personal
2. [PENDING] Prepare finance presentation - high - due 2027-10-20 - category university
3. [PENDING] Buy printer paper - medium - category personal
```

Tasks without a due date are placed at the end.

Each task displays its current status as `[PENDING]` or `[COMPLETED]`. Pending tasks with a due date earlier than today are also marked as `[OVERDUE]`.

### Filter tasks

The `list` command supports filtering by status and priority:

```bash
uv run task-manager list --status pending
uv run task-manager list --status completed
uv run task-manager list --status overdue
uv run task-manager list --priority high
```

Filters can also be combined with sorting:

```bash
uv run task-manager list --status pending --priority high --sort-by date
```

Filtering only changes which tasks are displayed; it does not modify the saved CSV file.


Tasks can also be filtered by category:

```bash
uv run task-manager list --category university
```

Category filtering is case-insensitive and ignores surrounding spaces.
It can be combined with status and priority filters:

```bash
uv run task-manager list --category university --status pending --priority high
```

Tasks with a custom category display it alongside their priority and due date.
The default category, `other`, is not displayed.



### Complete and reopen tasks

Mark a task as completed:

```bash
uv run task-manager done
```

The application displays the tasks and asks for the number of the task to complete. Its status changes from `pending` to `completed`.

To mark a completed task as pending again:

```bash
uv run task-manager reopen
```

The application asks for the number of the task to reopen.

Both commands update the task status in the CSV file without deleting the task.

### Recurring tasks

Add a task that repeats daily, weekly, or monthly with a required final date:

```bash
uv run task-manager add "Study Python" --due-date 2026-11-18 --repeat daily --repeat-until 2026-11-25
```

The first occurrence must have a due date. `--repeat-until` must be on or after
that date and is inclusive: an occurrence on the end date is created, but none
after it. When you complete a recurring task with `done`, the completed task
stays in the CSV and the next pending occurrence is created automatically.
Completing an overdue task skips missed dates; the next occurrence may be due
today, but will not be dated in the past. Reopening and completing a task again
does not create an identical next occurrence.

Recurrence intervals are fixed: `daily` repeats every 1 day, `weekly` every 7 days, and `monthly` every 30 days (not a calendar month).

For example, a monthly task due on January 31, 2026, will next be due on March 2, 2026.

### Tasks for today

Display pending tasks that are due today or overdue:

```bash
uv run task-manager today
```

Tasks are sorted by due date. Overdue tasks are marked as `[OVERDUE]`, while tasks due today are marked as `[DUE TODAY]`.

Completed tasks are excluded from this view.

### Upcoming tasks

Display pending tasks due within the next seven days:

```bash
uv run task-manager due-soon
```

This command includes tasks due from tomorrow through seven days from today, inclusive.

Tasks due today, overdue tasks, and completed tasks are excluded. Results are sorted by due date.


### Calendar view

Display tasks in a monthly calendar:

```bash
uv run task-manager calendar
```

By default, the calendar shows the current month and year. To view a specific month:

```bash
uv run task-manager calendar --month 11 --year 2026
```

The calendar displays a seven-column grid from Monday to Sunday. Days containing tasks show the number of tasks in brackets, such as `23 [2]` for two tasks due on November 23.

Below the calendar, an aligned table lists the tasks for the selected month, including their due date, title, status, and priority.

Both pending and completed tasks are included. Tasks without due dates or with deadlines outside the selected month are excluded.

Calendar view is read-only and does not modify saved tasks.

### Task summary

Display an overview of all saved tasks:

```bash
uv run task-manager summary
```

The summary includes:

- Total number of tasks.
- Pending and completed tasks.
- Number of overdue pending tasks.
- Completion rate as a percentage.
- Task counts by priority (`high`, `medium`, and `low`).

For example:

```text
Task Summary
------------
Total tasks: 5
Pending: 3
Completed: 2
Overdue: 1
Completion rate: 40.0%

Tasks by priority:
High: 2
Medium: 2
Low: 1
```

The summary includes both pending and completed tasks when counting priorities. It does not modify the CSV file.


### Delete a task

Run the delete command:

```bash
uv run task-manager delete
```

The application displays the current tasks and asks for the number of the task
to delete. The CSV file is then updated with the remaining tasks.


### Search tasks

Search saved tasks by a keyword in their title:

```bash
uv run task-manager search "study"
```

Search is case-insensitive and ignores spaces around the keyword.
Only matching tasks are displayed. Searching does not change saved data.

If nothing matches, the application displays `No matching tasks found.`
Blank keywords are rejected.


### Edit a task

Provide one or more fields to update:

```bash
uv run task-manager edit --title "Study Python" --priority high
```

The application displays tasks in priority order and asks for the number
of the task to edit. Changes are saved to the CSV file.
Fields not provided keep their current values.

To change a due date:

```bash
uv run task-manager edit --due-date 2026-11-10
```

To remove a due date:

```bash
uv run task-manager edit --due-date ""
```

To change a task's category:

```bash
uv run task-manager edit --category university
```

Invalid values, invalid task numbers and changes that would create an
exact duplicate are rejected without modifying saved data.
At least one field must be provided.

### Weekly review

Display an overview of overdue, due-today, upcoming, and completed tasks:

```bash
uv run task-manager weekly-review
```

The weekly review is divided into four sections:

- **Overdue tasks:** Pending tasks with a due date earlier than today.
- **Due today:** Pending tasks with a due date equal to today.
- **Upcoming – next 7 days:** Pending tasks due from tomorrow through seven days from today, inclusive.
- **Currently completed:** Total number of completed tasks.

Each section displays the number of tasks it contains. Tasks are listed with their title, priority, and due date.

If a section has no tasks, an appropriate message is displayed.

Completed tasks are excluded from the overdue, due-today, and upcoming sections. They are only included in the completed task count.

The weekly review is read-only and does not modify the saved CSV file.


### Task selection

When editing, deleting, completing, or reopening a task, enter the number shown in the displayed list.

Tasks are displayed in priority order, so these numbers represent temporary positions, not permanent task IDs.

Invalid selections do not modify saved tasks. Updating or deleting tasks preserves the original order of the remaining tasks in the CSV file.

## Command reference

| Command | Purpose | Inputs |
|---|---|---|
| `add` | Validates and saves a new task. | Required title; optional `--priority`, `--due-date`, and `--category`; for recurring tasks, `--repeat` and `--repeat-until` are required. |
| `list` | Displays saved tasks with optional sorting and filtering. | Optional `--sort-by`, `--status`, `--priority`, and `--category`. |
| `done` | Marks a selected task as completed. | Task number requested interactively. |
| `reopen` | Changes a completed task back to pending. | Task number requested interactively. |
| `delete` | Deletes a selected task. | Task number requested interactively. |
| `search` | Searches saved tasks by title, ignoring case. | Required keyword. |
| `edit` | Updates a selected task. | At least one of `--title`, `--priority`, `--due-date`, or `--category`. |
| `today` | Displays pending tasks due today or overdue. | No arguments. |
| `due-soon` | Displays pending tasks due in the next seven days, excluding today. | No arguments. |
| `weekly-review` | Displays overdue tasks, upcoming tasks, and the completed count. | No arguments. |
| `calendar` | Displays tasks due in a monthly calendar. | Optional `--month` and `--year`. |
| `summary` | Displays task statistics and completion rate. | No arguments. |

More information about any command is available through `--help`:

```bash
uv run task-manager --help
uv run task-manager add --help
uv run task-manager list --help
uv run task-manager done --help
uv run task-manager reopen --help
uv run task-manager delete --help
uv run task-manager search --help
uv run task-manager edit --help
uv run task-manager today --help
uv run task-manager due-soon --help
uv run task-manager summary --help
uv run task-manager calendar --help
uv run task-manager weekly-review --help
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

The CSV format depends on the types of tasks being stored.

Regular tasks are saved using five columns:

```text
title,priority,due_date,status,category
```

When recurring tasks are included, the CSV also stores their recurrence
frequency and final recurrence date:

```text
title,priority,due_date,status,recurrence,repeat_until,category
```

For recurring tasks:
- `due_date` identifies the scheduled date of the current occurrence.
- `recurrence` defines how often the task repeats: daily, weekly, or monthly.
- `repeat_until` defines the last date on which an occurrence can be scheduled.

All tasks in the same CSV file share the same columns. Fields that do
not apply to a task are stored with their default values or left empty.

The application also supports older CSV files containing non-recurring
tasks without a category column.


Tasks are marked as `pending` or `completed`. New tasks have `pending` status by default.

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
    edit_tasks.py
```

Responsibilities are separated as follows:

- `models.py` defines the `Task` data model.
- `validation.py` validates and normalises titles, priorities, and dates.
- `tasks.py` contains the task-management computations.
- `formatting.py` converts task data into displayable lines.
- `storage.py` reads and writes the CSV file.
- `cli.py` connects the core logic to terminal input and output.
- `__main__.py` provides the Python module entry point.
- `edit_tasks.py` contains the logic for editing existing tasks.

This follows a functional core / imperative shell design. Task computations
work with plain data and return results. File access and terminal output remain
outside the functional core.

Tests follow the same separation:

```text
tests/
    test_cli.py
    test_edit_tasks.py
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

## Run with Docker

You can run the task manager using Docker without installing Python or the project dependencies locally.

### Build the Docker image

```bash
docker build -t task-manager .
```

### Show available commands

```bash
docker run --rm task-manager --help
```

### Add a task

Use a named volume to persist task data between containers:

```bash
docker run --rm -v task-manager-data:/app/storage_tasks task-manager add "Study Finance" --priority high
```

### List saved tasks

```bash
docker run --rm -v task-manager-data:/app/storage_tasks task-manager list
```

The named volume `task-manager-data` stores tasks in `storage_tasks/tasks.csv`, ensuring that data persists even after a container is removed.

## Use of AI

ChatGPT and Codex (OpenAI) were used as support tools.

The existing task logic and tests from the earlier checkpoints were used as the starting point. ChatGPT was used to review this code, explain errors and suggest edge cases. The group manually entered and adapted the changes and reviewed the responsibility of each module.

For CSV persistence and duplicate detection, ChatGPT helped explain how tasks could be written to and read from storage_tasks/tasks.csv. It also suggested tests for saving multiple tasks, malformed CSV rows, exact duplicates, and persistence between CLI executions. The group reviewed the suggestions and tested the final behaviour locally.

For task deletion, task selection, and the list --sort-by date option, ChatGPT helped turn the intended behaviour into draft code and test cases. This included preserving CSV order when deleting tasks, refactoring shared selection logic for editing and deleting, and testing invalid user inputs. The group reviewed the suggested changes and verified the implementation using automated tests.

The wording and organisation of this README were drafted with ChatGPT. This included the installation instructions, command examples, storage explanation, project structure, development checks, and this AI disclosure. 

Codex was used to review the complete project against the partial-submission rubric and to identify missing tests, outdated documentation, and release requirements. The group made the final decisions about which suggestions to include and remains responsible for understanding and explaining the submitted code.
