# Functional core
import csv
import datetime
from dataclasses import dataclass

TITLE = 0
PRIORITY = 1
DUE_DATE = 2
FIELDS_PER_ROW = 3

VALID_PRIORITIES = ("low", "medium", "high")

PRIORITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}


@dataclass(frozen=True)
class Task:
    """A task with a title and priority."""

    title: str
    priority: str = "medium"
    due_date: str = ""


def normalize_due_date(due_date: str) -> str:
    normalized_due_date = due_date.strip()

    if normalized_due_date == "":
        return ""

    try:
        parsed_date = datetime.date.fromisoformat(normalized_due_date)
    except ValueError:
        raise ValueError("Due date must use YYYY-MM-DD.") from None

    if parsed_date.isoformat() != normalized_due_date:
        raise ValueError("Due date must use YYYY-MM-DD.")

    return normalized_due_date


def normalize_title(title: str) -> str:
    normalized_title = title.strip()

    if normalized_title == "":
        raise ValueError("Title cannot be empty.")

    return normalized_title


def normalize_priority(priority: str) -> str:
    normalized_priority = priority.strip().lower()

    if normalized_priority not in VALID_PRIORITIES:
        allowed = ", ".join(VALID_PRIORITIES)
        raise ValueError(f"Priority must be one of: {allowed}.")

    return normalized_priority


def create_task(
    title: str,
    priority: str = "medium",
    due_date: str = "",
) -> Task:
    return Task(
        title=normalize_title(title),
        priority=normalize_priority(priority),
        due_date=normalize_due_date(due_date),
    )


def read_tasks(path: str) -> list[Task]:
    tasks: list[Task] = []

    with open(path) as handle:
        reader = csv.reader(handle)
        next(reader)

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


def sort_tasks_by_priority(tasks: list[Task]) -> list[Task]:
    ordered = list(tasks)
    ordered.sort(key=lambda task: PRIORITY_ORDER[task.priority])
    return ordered


def add_task(
    tasks: list[Task],
    title: str,
    priority: str = "medium",
    due_date: str = "",
) -> Task:
    task = create_task(title, priority, due_date)
    tasks.append(task)
    return task


def view_tasks(tasks: list[Task]) -> list[str]:
    lines: list[str] = []

    for index, task in enumerate(tasks, start=1):
        line = f"{index}. {task.title} - {task.priority}"

        if task.due_date != "":
            line = f"{line} - due {task.due_date}"

        lines.append(line)

    return lines


def count_tasks_by_priority(tasks: list[Task]) -> dict[str, int]:
    count_of_prioties = {"high": 0, "medium": 0, "low": 0}
    for task in tasks:
        if task.priority == "high":
            count_of_prioties["high"] += 1
        elif task.priority == "medium":
            count_of_prioties["medium"] += 1
        elif task.priority == "low":
            count_of_prioties["low"] += 1
    return count_of_prioties
