import csv
import os
import tempfile
from pathlib import Path

from task_manager.models import InvalidNumberTasks, Task
from task_manager.tasks import create_task
from task_manager.tasks import delete_task as remove_task_from_list

TITLE = 0
PRIORITY = 1
DUE_DATE = 2
STATUS = 3
RECURRENCE = 4
REPEAT_UNTIL = 5
CATEGORY = 6

FIELDS_PER_ROW = 4

CSV_HEADER = ["title", "priority", "due_date", "status"]
RECURRING_HEADER = CSV_HEADER + ["recurrence"]
BOUNDED_HEADER = RECURRING_HEADER + ["repeat_until"]

CATEGORY_HEADER = CSV_HEADER + ["category"]
RECURRING_CATEGORY_HEADER = RECURRING_HEADER + ["category"]
BOUNDED_CATEGORY_HEADER = BOUNDED_HEADER + ["category"]

VALID_HEADERS = [
    CSV_HEADER,
    RECURRING_HEADER,
    BOUNDED_HEADER,
    CATEGORY_HEADER,
    RECURRING_CATEGORY_HEADER,
    BOUNDED_CATEGORY_HEADER,
]


def read_tasks(path: Path) -> list[Task]:
    tasks: list[Task] = []

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, strict=True)

        try:
            header = next(reader, None)

            if header not in VALID_HEADERS:
                raise ValueError("Invalid CSV header.")

            expected_columns = len(header)

            for row_number, row in enumerate(reader, start=2):
                if len(row) != expected_columns:
                    raise ValueError(
                        f"Invalid CSV row {row_number}: expected {expected_columns} columns."
                    )

                try:
                    task = create_task(
                        title=row[TITLE],
                        priority=row[PRIORITY],
                        due_date=row[DUE_DATE],
                        status=row[STATUS],
                        recurrence=row[RECURRENCE] if "recurrence" in header else "none",
                        repeat_until=row[REPEAT_UNTIL] if "repeat_until" in header else "",
                        category=row[header.index("category")] if "category" in header else "other",
                    )
                except ValueError as error:
                    raise ValueError(f"Invalid CSV row {row_number}: {error}") from error

                tasks.append(task)

        except csv.Error as error:
            raise ValueError(f"Invalid CSV syntax near line {reader.line_num}: {error}") from error

    return tasks


def append_task(path: Path, task: Task) -> None:
    tasks = read_tasks(path) if path.exists() and path.stat().st_size > 0 else []

    tasks.append(task)
    write_tasks(path, tasks)


def write_tasks(path: Path, tasks: list[Task]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)

            writer = csv.writer(handle)
            include_end_date = any(task.repeat_until for task in tasks)
            include_recurrence = include_end_date or any(
                task.recurrence != "none" for task in tasks
            )

            writer.writerow(
                BOUNDED_CATEGORY_HEADER
                if include_end_date
                else RECURRING_CATEGORY_HEADER
                if include_recurrence
                else CATEGORY_HEADER
            )

            for task in tasks:
                row = [task.title, task.priority, task.due_date, task.status]

                if include_recurrence:
                    row.append(task.recurrence)
                if include_end_date:
                    row.append(task.repeat_until)

                row.append(task.category)

                writer.writerow(row)

        os.replace(temporary_path, path)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def delete_task(path: Path, task_number: int) -> None:
    """Delete a stored task by its number, starting at 1."""
    tasks = read_tasks(path)

    try:
        _, remaining_tasks = remove_task_from_list(tasks, task_number)
    except InvalidNumberTasks as error:
        raise ValueError("Task number out of range.") from error

    write_tasks(path, remaining_tasks)
