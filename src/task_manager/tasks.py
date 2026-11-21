from calendar import monthrange
from collections.abc import Iterator
from dataclasses import replace
from datetime import date, timedelta

from task_manager.models import InvalidNumberTasks, Task
from task_manager.validation import (
    normalize_due_date,
    normalize_priority,
    normalize_recurrence,
    normalize_status,
    normalize_title,
)

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def create_task(
    title: str,
    priority: str = "medium",
    due_date: str = "",
    status: str = "pending",
    recurrence: str = "none",
    repeat_until: str = "",
    category: str = "other",
) -> Task:
    normalized_due_date = normalize_due_date(due_date)
    normalized_recurrence = normalize_recurrence(recurrence)
    normalized_repeat_until = normalize_due_date(repeat_until)

    if normalized_recurrence != "none" and not normalized_due_date:
        raise ValueError("Recurring tasks require a due date.")
    if normalized_repeat_until and normalized_recurrence == "none":
        raise ValueError("An end date requires a recurring task.")
    if normalized_repeat_until and normalized_repeat_until < normalized_due_date:
        raise ValueError("End date must be on or after the due date.")

    return Task(
        title=normalize_title(title),
        priority=normalize_priority(priority),
        due_date=normalized_due_date,
        status=normalize_status(status),
        recurrence=normalized_recurrence,
        repeat_until=normalized_repeat_until,
        category=category,
    )


def add_task(
    tasks: list[Task],
    title: str,
    priority: str = "medium",
    due_date: str = "",
    category: str = "other",
) -> Task:
    """Create a task, append it to the input list, and return the new task."""
    task = create_task(title, priority, due_date, category=category)
    tasks.append(task)
    return task


def filter_tasks_by_status(tasks: list[Task], status: str) -> list[Task]:
    if status not in ("pending", "completed", "all"):
        raise ValueError("Status must be one of: pending, completed, all.")

    if status == "all":
        return list(tasks)

    return [task for task in tasks if task.status == status]


def is_overdue(task: Task, today: date) -> bool:
    return (
        task.status == "pending"
        and task.due_date != ""
        and date.fromisoformat(task.due_date) < today
    )


def filter_overdue_tasks(tasks: list[Task], today: date) -> list[Task]:
    return [task for task in tasks if is_overdue(task, today)]


def _pending_tasks_with_due_dates(tasks: list[Task]) -> Iterator[tuple[Task, date]]:
    for task in tasks:
        if task.status == "pending" and task.due_date != "":
            yield task, date.fromisoformat(task.due_date)


def tasks_for_today(tasks: list[Task], today: date) -> list[Task]:
    """Return pending tasks due today or earlier, sorted by due date."""
    selected_tasks = [
        task for task, due_date in _pending_tasks_with_due_dates(tasks) if due_date <= today
    ]
    return sort_tasks_by_due_date(selected_tasks)


def tasks_due_today(tasks: list[Task], today: date) -> list[Task]:
    """Return pending tasks due exactly today."""
    selected_tasks = [
        task for task, due_date in _pending_tasks_with_due_dates(tasks) if due_date == today
    ]
    return sort_tasks_by_due_date(selected_tasks)


def tasks_due_soon(tasks: list[Task], today: date) -> list[Task]:
    """Return pending tasks due within the next seven days, excluding today."""
    selected_tasks = [
        task
        for task, due_date in _pending_tasks_with_due_dates(tasks)
        if 1 <= (due_date - today).days <= 7
    ]
    return sort_tasks_by_due_date(selected_tasks)


def task_summary(tasks: list[Task], today: date) -> dict[str, int | float]:
    """Calculate task statistics without modifying the original tasks."""
    total = len(tasks)
    pending = sum(task.status == "pending" for task in tasks)
    completed = sum(task.status == "completed" for task in tasks)
    overdue = len(filter_overdue_tasks(tasks, today))

    completion_rate = (completed / total * 100) if total > 0 else 0.0

    priorities = count_tasks_by_priority(tasks)

    return {
        "total": total,
        "pending": pending,
        "completed": completed,
        "overdue": overdue,
        "completion_rate": completion_rate,
        "high": priorities["high"],
        "medium": priorities["medium"],
        "low": priorities["low"],
    }


def sort_tasks_by_priority(tasks: list[Task]) -> list[Task]:
    ordered = list(tasks)
    ordered.sort(key=lambda task: PRIORITY_ORDER[task.priority])
    return ordered


def sort_tasks_by_due_date(tasks: list[Task]) -> list[Task]:
    return sorted(tasks, key=lambda task: (task.due_date == "", task.due_date))


def count_tasks_by_priority(tasks: list[Task]) -> dict[str, int]:
    count_of_priorities = {"high": 0, "medium": 0, "low": 0}

    for task in tasks:
        count_of_priorities[task.priority] += 1

    return count_of_priorities


def remove_duplicate_tasks(tasks: list[Task]) -> list[Task]:
    unique_tasks: list[Task] = []

    for task in tasks:
        if not is_duplicate(task, unique_tasks):
            unique_tasks.append(task)

    return unique_tasks


def is_duplicate(new_task: Task, tasks: list[Task]) -> bool:
    return any(
        task.title == new_task.title
        and task.priority == new_task.priority
        and task.due_date == new_task.due_date
        for task in tasks
    )


def delete_task(tasks: list[Task], task_number: int) -> tuple[Task, list[Task]]:
    if task_number < 1 or task_number > len(tasks):
        raise InvalidNumberTasks("Task number does not exist.")

    remaining_tasks = list(tasks)

    deleted_task = remaining_tasks.pop(task_number - 1)

    return deleted_task, remaining_tasks


def get_original_task_number(
    tasks: list[Task],
    displayed_tasks: list[Task],
    task_number: int,
) -> int:
    if task_number < 1 or task_number > len(displayed_tasks):
        raise InvalidNumberTasks("Task number does not exist.")

    selected_task = displayed_tasks[task_number - 1]

    for index, task in enumerate(tasks, start=1):
        if task is selected_task:
            return index

    raise InvalidNumberTasks("Task number does not exist.")


def search_tasks(tasks: list[Task], keyword: str) -> list[Task]:
    return [task for task in tasks if keyword.lower() in task.title.lower()]


def complete_task(
    tasks: list[Task], task_number: int, today: date | None = None
) -> tuple[Task, list[Task]]:
    if task_number < 1 or task_number > len(tasks):
        raise InvalidNumberTasks("Task number does not exist.")

    original_task = tasks[task_number - 1]

    if original_task.status == "completed":
        raise ValueError("Task is already completed.")

    completed_task = replace(original_task, status="completed")

    updated_tasks = list(tasks)
    updated_tasks[task_number - 1] = completed_task

    if original_task.recurrence != "none":
        due = date.fromisoformat(original_task.due_date)
        next_date = next_occurrence(due, original_task.recurrence, today)

        if next_date is not None and (
            not original_task.repeat_until
            or next_date <= date.fromisoformat(original_task.repeat_until)
        ):
            next_task = replace(original_task, due_date=next_date.isoformat())

            if not any(
                task.title == next_task.title
                and task.priority == next_task.priority
                and task.due_date == next_task.due_date
                and task.recurrence == next_task.recurrence
                and task.repeat_until == next_task.repeat_until
                for task in updated_tasks
            ):
                updated_tasks.append(next_task)

    return completed_task, updated_tasks


def next_occurrence(due: date, recurrence: str, today: date | None = None) -> date | None:
    """Find the next scheduled date, skipping missed occurrences when given today."""
    if recurrence in ("daily", "weekly"):
        interval = 1 if recurrence == "daily" else 7
        days_to_today = (today - due).days if today else 0
        steps = max(1, (days_to_today + interval - 1) // interval)
        try:
            return due + timedelta(days=interval * steps)
        except OverflowError:
            return None

    if recurrence == "monthly":
        months = 1
        if today and today > due:
            months = max(1, (today.year - due.year) * 12 + today.month - due.month)
        while True:
            month_index = due.year * 12 + due.month - 1 + months
            year, zero_month = divmod(month_index, 12)
            if year > 9999:
                return None
            candidate = date(
                year, zero_month + 1, min(due.day, monthrange(year, zero_month + 1)[1])
            )
            if today is None or candidate >= today:
                return candidate
            months += 1

    raise ValueError("Invalid recurrence.")


def reopen_task(tasks: list[Task], task_number: int) -> tuple[Task, list[Task]]:
    if task_number < 1 or task_number > len(tasks):
        raise InvalidNumberTasks("Task number does not exist.")

    original_task = tasks[task_number - 1]

    if original_task.status == "pending":
        raise ValueError("Task is already pending.")

    reopened_task = replace(original_task, status="pending")

    updated_tasks = list(tasks)
    updated_tasks[task_number - 1] = reopened_task

    return reopened_task, updated_tasks


def filter_tasks_by_priority(tasks: list[Task], priority: str) -> list[Task]:
    if priority not in ("high", "medium", "low", "all"):
        raise ValueError("Priority filter must be one of: high, medium, low, all.")

    if priority == "all":
        return list(tasks)

    return [task for task in tasks if task.priority == priority]


def weekly_review(
    tasks: list[Task],
    today: date,
) -> tuple[list[Task], list[Task], list[Task], int]:
    """Return overdue, due-today, upcoming tasks and completed count."""

    overdue_tasks = filter_overdue_tasks(tasks, today)

    due_today_tasks = tasks_due_today(tasks, today)

    upcoming_tasks = tasks_due_soon(tasks, today)

    completed_count = sum(task.status == "completed" for task in tasks)

    return overdue_tasks, due_today_tasks, upcoming_tasks, completed_count
