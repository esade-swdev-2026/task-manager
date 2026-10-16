from pathlib import Path

from task_manager.models import Task
from task_manager.storage import (
    append_task,
    read_tasks,
    write_tasks,
)


def test_append_task_creates_csv_and_saves_task(
    tmp_path: Path,
) -> None:
    path = tmp_path / "storage_tasks" / "tasks.csv"

    task = Task(
        "Study Finance",
        "high",
        "2026-10-20",
    )

    append_task(path, task)

    assert path.exists()
    assert read_tasks(path) == [task]


def test_append_task_keeps_existing_tasks(
    tmp_path: Path,
) -> None:
    path = tmp_path / "storage_tasks" / "tasks.csv"

    first = Task("First task", "high")
    second = Task("Second task", "low")

    append_task(path, first)
    append_task(path, second)

    assert read_tasks(path) == [
        first,
        second,
    ]


def test_read_tasks_skips_broken_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "tasks.csv"

    path.write_text(
        "title,priority,due_date\n"
        "Study Finance,high,2026-10-20\n"
        "broken row\n"
        "Buy groceries,medium,\n",
        encoding="utf-8",
    )

    assert read_tasks(path) == [
        Task(
            "Study Finance",
            "high",
            "2026-10-20",
        ),
        Task(
            "Buy groceries",
            "medium",
            "",
        ),
    ]


def test_write_tasks_replaces_previous_contents(
    tmp_path: Path,
) -> None:
    path = tmp_path / "storage_tasks" / "tasks.csv"

    append_task(
        path,
        Task("Old task", "low"),
    )

    new_tasks = [
        Task(
            "New task",
            "high",
            "2026-10-20",
        )
    ]

    write_tasks(path, new_tasks)

    assert read_tasks(path) == new_tasks
