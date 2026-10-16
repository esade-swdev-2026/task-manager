from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """A task with a title, priority and due date."""

    title: str
    priority: str = "medium"
    due_date: str = ""
