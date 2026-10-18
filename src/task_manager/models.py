from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """A task with a title, priority and due date."""

    title: str
    priority: str = "medium"
    due_date: str = ""


class EmptyTitleError(ValueError):
    pass


class TaskNotFoundError(LookupError):
    pass


class DuplicateTaskError(ValueError):
    pass


class InvalidPriority(ValueError):
    pass


class InvalidDueDate(ValueError):
    pass


class InvalidNumberTasks(ValueError):
    pass
