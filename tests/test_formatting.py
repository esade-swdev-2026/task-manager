from task_manager.formatting import view_tasks
from task_manager.models import Task


def test_view_tasks() -> None:
    tasks = [
        Task("Study Finance", "high"),
        Task("Buy groceries", "medium"),
    ]

    assert view_tasks(tasks) == [
        "1. Study Finance - high",
        "2. Buy groceries - medium",
    ]


def test_view_task_with_due_date() -> None:
    tasks = [
        Task(
            "Submit assignment",
            "high",
            "2026-10-18",
        )
    ]

    assert view_tasks(tasks) == [
        ("1. Submit assignment - high - due 2026-10-18"),
    ]


def test_view_tasks_empty() -> None:
    assert view_tasks([]) == []
