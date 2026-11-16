import csv
import os
import tempfile
from pathlib import Path

from task_manager.models import Task
from task_manager.tasks import create_task

TITLE = 0
PRIORITY = 1
DUE_DATE = 2
FIELDS_PER_ROW = 3

CSV_HEADER = ["title", "priority", "due_date"]


def read_tasks(path: Path) -> list[Task]:
    tasks: list[Task] = []

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, strict=True)

        try:
            header = next(reader, None)

            if header != CSV_HEADER:
                raise ValueError("Invalid CSV header.")

            for row_number, row in enumerate(reader, start=2):
                if len(row) != FIELDS_PER_ROW:
                    raise ValueError(
                        f"Invalid CSV row {row_number}: expected {FIELDS_PER_ROW} columns."
                    )

                try:
                    task = create_task(
                        title=row[TITLE],
                        priority=row[PRIORITY],
                        due_date=row[DUE_DATE],
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
            writer.writerow(CSV_HEADER)

            for task in tasks:
                writer.writerow([task.title, task.priority, task.due_date])

        os.replace(temporary_path, path)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def delete_task(path: Path, task_number: int) -> None:
    """Delete a stored task by its number, starting at 1."""
    tasks = read_tasks(path)

    if task_number < 1 or task_number > len(tasks):
        raise ValueError("Task number out of range.")

    del tasks[task_number - 1]
    write_tasks(path, tasks)
