from pathlib import Path

import pytest
from typer.testing import CliRunner

from task_manager.cli import app
from task_manager.models import Task
from task_manager.storage import read_tasks

runner = CliRunner()


def test_add_task_default_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["add", "Study Finance"],
    )

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert result.exit_code == 0
    assert saved_tasks == [Task("Study Finance", "medium", "")]


def test_add_task_with_priority_and_due_date(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "add",
            "Submit assignment",
            "--priority",
            "high",
            "--due-date",
            "2026-10-18",
        ],
    )

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert result.exit_code == 0
    assert saved_tasks == [
        Task(
            "Submit assignment",
            "high",
            "2026-10-18",
        )
    ]


def test_duplicate_task_is_not_saved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    arguments = [
        "add",
        "Study Finance",
        "--priority",
        "high",
        "--due-date",
        "2026-10-20",
    ]

    first = runner.invoke(app, arguments)
    duplicate = runner.invoke(app, arguments)

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert first.exit_code == 0
    assert duplicate.exit_code == 1
    assert "Task already exists." in duplicate.stderr
    assert saved_tasks == [
        Task(
            "Study Finance",
            "high",
            "2026-10-20",
        )
    ]


def test_list_tasks_are_sorted_by_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    runner.invoke(
        app,
        ["add", "Low task", "--priority", "low"],
    )
    runner.invoke(
        app,
        ["add", "High task", "--priority", "high"],
    )
    runner.invoke(
        app,
        [
            "add",
            "Medium task",
            "--priority",
            "medium",
        ],
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. High task - high",
        "2. Medium task - medium",
        "3. Low task - low",
    ]


def test_list_tasks_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "No tasks found." in result.output


def test_invalid_priority_has_no_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "add",
            "Impossible task",
            "--priority",
            "urgent",
        ],
    )

    assert result.exit_code == 1
    assert "Priority must be one of: low, medium, high." in result.stderr
    assert "Traceback" not in result.output


def test_invalid_due_date_has_no_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "add",
            "Impossible task",
            "--due-date",
            "18-10-2026",
        ],
    )

    assert result.exit_code == 1
    assert "Due date must use YYYY-MM-DD." in result.stderr
    assert "Traceback" not in result.output


def test_delete_removes_task_shown_by_list_number(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    runner.invoke(
        app,
        [
            "add",
            "Low task",
            "--priority",
            "low",
        ],
    )
    runner.invoke(
        app,
        [
            "add",
            "High task",
            "--priority",
            "high",
        ],
    )

    result = runner.invoke(
        app,
        ["delete"],
        input="1\n",
    )

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert result.exit_code == 0
    assert "1. High task - high" in result.output
    assert "2. Low task - low" in result.output
    assert "deleted High task" in result.output
    assert saved_tasks == [Task("Low task", "low")]


def test_delete_when_no_tasks_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["delete"],
    )

    assert result.exit_code == 1
    assert "No tasks found." in result.stderr
    assert "Traceback" not in result.output


def test_list_tasks_are_sorted_by_due_date(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    runner.invoke(
        app,
        [
            "add",
            "No date task",
            "--priority",
            "high",
        ],
    )
    runner.invoke(
        app,
        [
            "add",
            "Late task",
            "--priority",
            "high",
            "--due-date",
            "2026-12-01",
        ],
    )
    runner.invoke(
        app,
        [
            "add",
            "Early task",
            "--priority",
            "low",
            "--due-date",
            "2026-10-01",
        ],
    )

    result = runner.invoke(
        app,
        [
            "list",
            "--sort-by",
            "date",
        ],
    )

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. Early task - low - due 2026-10-01",
        "2. Late task - high - due 2026-12-01",
        "3. No date task - high",
    ]


def test_list_rejects_invalid_sort_option(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "list",
            "--sort-by",
            "name",
        ],
    )

    assert result.exit_code == 1
    assert "Sort must be one of: priority, date." in result.stderr
    assert "Traceback" not in result.output
