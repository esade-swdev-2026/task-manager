from pathlib import Path

import pytest
from typer.testing import CliRunner

from task_manager.cli import app
from task_manager.tasks import Task, read_tasks

runner = CliRunner()


def test_add_task_default_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "Study Finance"])
    saved_tasks = read_tasks("data/tasks.csv")

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
    saved_tasks = read_tasks("data/tasks.csv")

    assert result.exit_code == 0
    assert saved_tasks == [
        Task("Submit assignment", "high", "2026-10-18"),
    ]


def test_list_tasks_are_sorted_by_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["add", "Low task", "--priority", "low"])
    runner.invoke(app, ["add", "High task", "--priority", "high"])
    runner.invoke(app, ["add", "Medium task", "--priority", "medium"])

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
        ["add", "Impossible task", "--priority", "urgent"],
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
        ["add", "Impossible task", "--due-date", "18-10-2026"],
    )

    assert result.exit_code == 1
    assert "Due date must use YYYY-MM-DD." in result.stderr
    assert "Traceback" not in result.output
