from task_manager.models import Task
from task_manager.validation import (
    normalize_due_date,
    normalize_priority,
    normalize_title,
)

PRIORITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}


def create_task(title: str, priority: str = "medium", due_date: str = "") -> Task:
    return Task(
        title=normalize_title(title),
        priority=normalize_priority(priority),
        due_date=normalize_due_date(due_date),
    )


def add_task(tasks: list[Task], title: str, priority: str = "medium", due_date: str = "") -> Task:
    task = create_task(title, priority, due_date)
    tasks.append(task)
    return task


def sort_tasks_by_priority(tasks: list[Task]) -> list[Task]:
    ordered = list(tasks)
    ordered.sort(key=lambda task: PRIORITY_ORDER[task.priority])
    return ordered


def sort_tasks_by_due_date(tasks: list[Task]) -> list[Task]:
    return sorted(
        tasks,
        key=lambda task: (
            task.due_date == "",
            task.due_date,
        ),
    )


def count_tasks_by_priority(tasks: list[Task]) -> dict[str, int]:
    count_of_priorities = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for task in tasks:
        count_of_priorities[task.priority] += 1

    return count_of_priorities


def remove_duplicate_tasks(tasks: list[Task]) -> list[Task]:
    return list(dict.fromkeys(tasks))


def is_duplicate(new_task: Task, tasks: list[Task]) -> bool:
    return new_task in tasks


def delete_task(tasks: list[Task], task_number: int) -> tuple[Task, list[Task]]:
    if task_number < 1 or task_number > len(tasks):
        raise ValueError("Task number does not exist.")

    remaining_tasks = list(tasks)

    deleted_task = remaining_tasks.pop(task_number - 1)

    return deleted_task, remaining_tasks
