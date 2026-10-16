import csv
from pathlib import Path

from task_manager.models import Task
from task_manager.tasks import create_task

TITLE = 0
PRIORITY = 1
DUE_DATE = 2
FIELDS_PER_ROW = 3

CSV_HEADER = [
    "title",
    "priority",
    "due_date",
]


def read_tasks(path: Path) -> list[Task]:
    tasks: list[Task] = []

    with path.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.reader(handle)
        next(reader, None)

        for row in reader:
            if len(row) == FIELDS_PER_ROW:
                tasks.append(
                    create_task(
                        title=row[TITLE],
                        priority=row[PRIORITY],
                        due_date=row[DUE_DATE],
                    )
                )

    return tasks


def append_task(
    path: Path,
    task: Task,
) -> None:
    path.parent.mkdir(exist_ok=True)

    is_new = not path.exists() or path.stat().st_size == 0

    with path.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle)

        if is_new:
            writer.writerow(CSV_HEADER)

        writer.writerow(
            [
                task.title,
                task.priority,
                task.due_date,
            ]
        )


def write_tasks(
    path: Path,
    tasks: list[Task],
) -> None:
    path.parent.mkdir(exist_ok=True)

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)

        for task in tasks:
            writer.writerow(
                [
                    task.title,
                    task.priority,
                    task.due_date,
                ]
            )
