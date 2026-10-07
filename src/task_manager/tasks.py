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