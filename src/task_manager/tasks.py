# Functional core

from dataclasses import dataclass


@dataclass
class Task:
    title: str
    priority: str = "medium"


def add_task(tasks: list[Task], title: str, priority: str = "medium") -> Task:
    task = Task(title=title, priority=priority)
    tasks.append(task)
    return task


def view_tasks(tasks: list[Task]) -> list[str]:
    return [f"{index}. {task.title} - {task.priority}" for index, task in enumerate(tasks, start=1)]


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
