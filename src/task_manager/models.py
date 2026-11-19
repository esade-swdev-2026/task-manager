from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """A task with a title, priority, due date, status and recurrence."""

    title: str
    priority: str = "medium"
    due_date: str = ""
    status: str = "pending"
    recurrence: str = "none"
    repeat_until: str = ""
    category: str = "other"


class EmptyTitleError(ValueError):
    pass


class InvalidPriority(ValueError):
    pass


class InvalidDueDate(ValueError):
    pass


class InvalidNumberTasks(ValueError):
    pass


class InvalidStatus(ValueError):
    pass
