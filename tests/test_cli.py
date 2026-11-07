from pathlib import Path

import pytest
from typer.testing import CliRunner

from task_manager.cli import app
from task_manager.models import Task
from task_manager.storage import read_tasks

runner = CliRunner()


def test_add_task_default_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "Study Finance"])
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
        ["add", "Submit assignment", "--priority", "high", "--due-date", "2026-10-18"],
    )

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert result.exit_code == 0
    assert saved_tasks == [Task("Submit assignment", "high", "2026-10-18")]


def test_duplicate_task_is_not_saved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    assert saved_tasks == [Task("Study Finance", "high", "2026-10-20")]


def test_list_tasks_are_sorted_by_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_list_tasks_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "No tasks found." in result.output


def test_invalid_priority_has_no_traceback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "Impossible task", "--priority", "urgent"])

    assert result.exit_code == 1
    assert "Priority must be one of: low, medium, high." in result.stderr
    assert "Traceback" not in result.output


def test_invalid_due_date_has_no_traceback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "Impossible task", "--due-date", "18-10-2026"])

    assert result.exit_code == 1
    assert "Due date must use YYYY-MM-DD." in result.stderr
    assert "Traceback" not in result.output


def test_delete_removes_task_shown_by_list_number(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["add", "Low task", "--priority", "low"])
    runner.invoke(app, ["add", "High task", "--priority", "high"])

    result = runner.invoke(app, ["delete"], input="1\n")
    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert result.exit_code == 0
    assert "1. High task - high" in result.output
    assert "2. Low task - low" in result.output
    assert "deleted High task" in result.output
    assert saved_tasks == [Task("Low task", "low")]


def test_delete_when_no_tasks_exist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["delete"])

    assert result.exit_code == 1
    assert "No tasks found." in result.stderr
    assert "Traceback" not in result.output


def test_list_tasks_are_sorted_by_due_date(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["add", "No date task", "--priority", "high"])
    runner.invoke(
        app,
        ["add", "Late task", "--priority", "high", "--due-date", "2026-12-01"],
    )
    runner.invoke(
        app,
        ["add", "Early task", "--priority", "low", "--due-date", "2026-10-01"],
    )

    result = runner.invoke(app, ["list", "--sort-by", "date"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. Early task - low - due 2026-10-01",
        "2. Late task - high - due 2026-12-01",
        "3. No date task - high",
    ]


def test_list_rejects_invalid_sort_option(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["list", "--sort-by", "name"])

    assert result.exit_code == 1
    assert "Sort must be one of: priority, date." in result.stderr
    assert "Traceback" not in result.output


def test_priority_counts_and_sorts_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["add", "Low task", "--priority", "low"])
    runner.invoke(app, ["add", "High task", "--priority", "high"])
    runner.invoke(app, ["add", "Medium task", "--priority", "medium"])
    runner.invoke(app, ["add", "Another high task", "--priority", "high"])

    result = runner.invoke(app, ["priority"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "Tasks by priority:",
        "High: 2",
        "Medium: 1",
        "Low: 1",
        "",
        "Tasks sorted by priority:",
        "1. High task - high",
        "2. Another high task - high",
        "3. Medium task - medium",
        "4. Low task - low",
    ]


def test_priority_when_no_tasks_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["priority"])

    assert result.exit_code == 0
    assert "No tasks found." in result.output


def test_priority_with_only_high_priority_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["add", "First task", "--priority", "high"])
    runner.invoke(app, ["add", "Second task", "--priority", "high"])

    result = runner.invoke(app, ["priority"])

    assert result.exit_code == 0
    assert "High: 2" in result.output
    assert "Medium: 0" in result.output
    assert "Low: 0" in result.output
    assert "1. First task - high" in result.output
    assert "2. Second task - high" in result.output


def test_edit_updates_selected_task_and_preserves_other_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "Low task", "--priority", "low"])
    runner.invoke(
        app,
        ["add", "High task", "--priority", "high", "--due-date", "2026-11-10"],
    )

    result = runner.invoke(app, ["edit", "--title", "Updated task"], input="1\n")

    assert result.exit_code == 0
    assert "1. High task - high" in result.output
    assert read_tasks(Path("storage_tasks/tasks.csv")) == [
        Task("Low task", "low"),
        Task("Updated task", "high", "2026-11-10"),
    ]


def test_edit_changes_all_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "Original"])

    result = runner.invoke(
        app,
        ["edit", "--title", "Updated", "--priority", "high", "--due-date", "2026-11-10"],
        input="1\n",
    )

    assert result.exit_code == 0
    assert read_tasks(Path("storage_tasks/tasks.csv")) == [
        Task("Updated", "high", "2026-11-10"),
    ]


def test_edit_clears_due_date(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "Study", "--due-date", "2026-11-10"])

    result = runner.invoke(app, ["edit", "--due-date", ""], input="1\n")

    assert result.exit_code == 0
    assert read_tasks(Path("storage_tasks/tasks.csv")) == [Task("Study")]


@pytest.mark.parametrize(
    ("options", "selection", "message"),
    [
        (["--title", "Updated"], "0\n", "Task number does not exist."),
        (["--title", "   "], "1\n", "Title cannot be empty."),
        (["--priority", "urgent"], "1\n", "Priority must be one of"),
        (["--due-date", "invalid"], "1\n", "Due date must use YYYY-MM-DD."),
        (["--title", "Other"], "1\n", "Task already exists."),
        ([], "", "Provide at least one field to edit."),
    ],
)
def test_edit_rejects_invalid_changes_without_modifying_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options: list[str],
    selection: str,
    message: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "Original"])
    runner.invoke(app, ["add", "Other"])
    path = Path("storage_tasks/tasks.csv")
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["edit", *options], input=selection)

    assert result.exit_code == 1
    assert message in result.stderr
    assert path.read_bytes() == original_contents


def test_edit_without_saved_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["edit", "--title", "Updated"])

    assert result.exit_code == 1
    assert "No tasks found." in result.stderr
    assert not Path("storage_tasks/tasks.csv").exists()


def test_edit_priority_preserves_file_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "Low", "--priority", "low"])
    runner.invoke(app, ["add", "High", "--priority", "high"])
    runner.invoke(app, ["add", "Medium", "--priority", "medium"])

    result = runner.invoke(app, ["edit", "--priority", "low"], input="1\n")

    assert result.exit_code == 0
    assert "1. High - high" in result.output
    assert read_tasks(Path("storage_tasks/tasks.csv")) == [
        Task("Low", "low"),
        Task("High", "low"),
        Task("Medium", "medium"),
    ]
    displayed = runner.invoke(app, ["priority"])
    assert "1. Medium - medium" in displayed.output
    assert "2. Low - low" in displayed.output
    assert "3. High - low" in displayed.output
