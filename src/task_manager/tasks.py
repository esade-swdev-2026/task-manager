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