import csv
from datetime import date
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

import task_manager.cli as cli
from task_manager.cli import app
from task_manager.models import Task
from task_manager.storage import read_tasks, write_tasks

runner = CliRunner()


def test_load_tasks_or_exit_returns_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_tasks = [Task("Study Finance", "high", "")]

    monkeypatch.setattr(cli, "read_tasks", lambda path: expected_tasks)

    result = cli.load_tasks_or_exit(tmp_path / "tasks.csv")

    assert result == expected_tasks


def test_load_tasks_or_exit_returns_empty_list_when_file_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_file_not_found(path: Path) -> list[Task]:
        raise FileNotFoundError("file not found")

    monkeypatch.setattr(cli, "read_tasks", raise_file_not_found)

    result = cli.load_tasks_or_exit(tmp_path / "tasks.csv")

    assert result == []


def test_load_tasks_or_exit_handles_invalid_csv_header(
    tmp_path: Path,
) -> None:
    path = tmp_path / "tasks.csv"
    path.write_text("invalid,header\n", encoding="utf-8")

    with pytest.raises(typer.Exit) as exc_info:
        cli.load_tasks_or_exit(path)

    assert exc_info.value.exit_code == 1


@pytest.mark.parametrize(
    ("error_type", "error_message"),
    [
        (PermissionError, "Permission denied"),
        (OSError, "Input/output error"),
        (ValueError, "Invalid CSV data"),
        (csv.Error, "Malformed CSV"),
    ],
)
def test_load_tasks_or_exit_handles_read_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error_type: type[Exception],
    error_message: str,
) -> None:
    path = tmp_path / "tasks.csv"

    def raise_read_error(file_path: Path) -> list[Task]:
        raise error_type(error_message)

    monkeypatch.setattr(cli, "read_tasks", raise_read_error)

    with pytest.raises(typer.Exit) as exc_info:
        cli.load_tasks_or_exit(path)

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 1
    assert f"could not read {path}: {error_message}" in captured.err


@pytest.mark.parametrize(
    "arguments",
    [
        ["add", "New task"],
        ["list"],
        ["delete"],
        ["priority"],
        ["search", "study"],
        ["edit", "--title", "Updated task"],
    ],
)
def test_commands_handle_csv_read_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    def raise_read_error(path: Path) -> list[Task]:
        raise PermissionError("Permission denied")

    monkeypatch.setattr(cli, "read_tasks", raise_read_error)

    result = runner.invoke(app, arguments)

    assert result.exit_code == 1
    assert "could not read" in result.stderr
    assert "Permission denied" in result.stderr
    assert "Traceback" not in result.output


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

    assert runner.invoke(app, ["add", "Low task", "--priority", "low"]).exit_code == 0
    assert runner.invoke(app, ["add", "High task", "--priority", "high"]).exit_code == 0
    assert runner.invoke(app, ["add", "Medium task", "--priority", "medium"]).exit_code == 0

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] High task - high",
        "2. [PENDING] Medium task - medium",
        "3. [PENDING] Low task - low",
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

    assert runner.invoke(app, ["add", "Low task", "--priority", "low"]).exit_code == 0
    assert runner.invoke(app, ["add", "High task", "--priority", "high"]).exit_code == 0

    result = runner.invoke(app, ["delete"], input="1\n")
    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert result.exit_code == 0
    assert "1. [PENDING] High task - high" in result.output
    assert "2. [PENDING] Low task - low" in result.output
    assert "deleted High task" in result.output
    assert saved_tasks == [Task("Low task", "low")]


def test_delete_preserves_original_csv_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    low = runner.invoke(app, ["add", "Low task", "--priority", "low"])
    high = runner.invoke(app, ["add", "High task", "--priority", "high"])
    medium = runner.invoke(app, ["add", "Medium task", "--priority", "medium"])

    assert low.exit_code == 0
    assert high.exit_code == 0
    assert medium.exit_code == 0

    result = runner.invoke(app, ["delete"], input="1\n")

    assert result.exit_code == 0
    assert "1. [PENDING] High task - high" in result.output
    assert "deleted High task" in result.output

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert saved_tasks == [
        Task("Low task", "low", ""),
        Task("Medium task", "medium", ""),
    ]


def test_delete_when_no_tasks_exist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["delete"])

    assert result.exit_code == 1
    assert "No tasks found." in result.stderr
    assert "Traceback" not in result.output


def test_list_tasks_are_sorted_by_due_date(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 1, 1))

    assert runner.invoke(app, ["add", "No date task", "--priority", "high"]).exit_code == 0

    assert (
        runner.invoke(
            app,
            ["add", "Late task", "--priority", "high", "--due-date", "2026-12-01"],
        ).exit_code
        == 0
    )

    assert (
        runner.invoke(
            app,
            ["add", "Early task", "--priority", "low", "--due-date", "2026-10-01"],
        ).exit_code
        == 0
    )

    result = runner.invoke(app, ["list", "--sort-by", "date"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] Early task - low - due 2026-10-01",
        "2. [PENDING] Late task - high - due 2026-12-01",
        "3. [PENDING] No date task - high",
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

    assert runner.invoke(app, ["add", "Low task", "--priority", "low"]).exit_code == 0
    assert runner.invoke(app, ["add", "High task", "--priority", "high"]).exit_code == 0
    assert runner.invoke(app, ["add", "Medium task", "--priority", "medium"]).exit_code == 0
    assert runner.invoke(app, ["add", "Another high task", "--priority", "high"]).exit_code == 0

    result = runner.invoke(app, ["priority"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "Tasks by priority:",
        "High: 2",
        "Medium: 1",
        "Low: 1",
        "",
        "Tasks sorted by priority:",
        "1. [PENDING] High task - high",
        "2. [PENDING] Another high task - high",
        "3. [PENDING] Medium task - medium",
        "4. [PENDING] Low task - low",
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

    assert runner.invoke(app, ["add", "First task", "--priority", "high"]).exit_code == 0
    assert runner.invoke(app, ["add", "Second task", "--priority", "high"]).exit_code == 0

    result = runner.invoke(app, ["priority"])

    assert result.exit_code == 0
    assert "High: 2" in result.output
    assert "Medium: 0" in result.output
    assert "Low: 0" in result.output
    assert "1. [PENDING] First task - high" in result.output
    assert "2. [PENDING] Second task - high" in result.output


def test_edit_updates_selected_task_and_preserves_other_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 1, 1))
    assert runner.invoke(app, ["add", "Low task", "--priority", "low"]).exit_code == 0

    assert (
        runner.invoke(
            app,
            ["add", "High task", "--priority", "high", "--due-date", "2026-11-10"],
        ).exit_code
        == 0
    )
    result = runner.invoke(app, ["edit", "--title", "Updated task"], input="1\n")

    assert result.exit_code == 0
    assert "1. [PENDING] High task - high" in result.output
    assert read_tasks(Path("storage_tasks/tasks.csv")) == [
        Task("Low task", "low"),
        Task("Updated task", "high", "2026-11-10"),
    ]


def test_edit_changes_all_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["add", "Original"]).exit_code == 0

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
    assert runner.invoke(app, ["add", "Study", "--due-date", "2026-11-10"]).exit_code == 0

    result = runner.invoke(app, ["edit", "--due-date", ""], input="1\n")

    assert result.exit_code == 0
    assert read_tasks(Path("storage_tasks/tasks.csv")) == [Task("Study")]


@pytest.mark.parametrize(
    ("options", "selection", "message"),
    [
        (["--title", "Updated"], "0\n", "Task number does not exist."),
        (["--title", "Updated"], "-1\n", "Task number does not exist."),
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
    assert runner.invoke(app, ["add", "Original"]).exit_code == 0
    assert runner.invoke(app, ["add", "Other"]).exit_code == 0
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
    assert runner.invoke(app, ["add", "Low", "--priority", "low"]).exit_code == 0
    assert runner.invoke(app, ["add", "High", "--priority", "high"]).exit_code == 0
    assert runner.invoke(app, ["add", "Medium", "--priority", "medium"]).exit_code == 0

    result = runner.invoke(app, ["edit", "--priority", "low"], input="1\n")

    assert result.exit_code == 0
    assert "1. [PENDING] High - high" in result.output
    assert read_tasks(Path("storage_tasks/tasks.csv")) == [
        Task("Low", "low"),
        Task("High", "low"),
        Task("Medium", "medium"),
    ]
    displayed = runner.invoke(app, ["priority"])
    assert "1. [PENDING] Medium - medium" in displayed.output
    assert "2. [PENDING] Low - low" in displayed.output
    assert "3. [PENDING] High - low" in displayed.output


def test_edit_with_no_task_number_does_not_do_anything(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["add", "Original"]).exit_code == 0

    path = Path("storage_tasks/tasks.csv")
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["edit", "--title", "Updated"])

    assert result.exit_code == 1
    assert path.read_bytes() == original_contents


def test_edit_rejects_text_as_task_number(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["add", "Original"]).exit_code == 0
    path = Path("storage_tasks/tasks.csv")
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["edit", "--title", "Updated"], input="abc\n")

    assert result.exit_code == 1
    assert "Invalid task number." in result.stderr
    assert path.read_bytes() == original_contents


def test_edit_rejects_task_number_out_of_range(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["add", "Original"]).exit_code == 0
    path = Path("storage_tasks/tasks.csv")
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["edit", "--title", "Updated"], input="2\n")

    assert result.exit_code == 1
    assert "Task number does not exist." in result.stderr
    assert path.read_bytes() == original_contents


def test_search_matches_titles_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["add", "Buy groceries", "--priority", "high"]).exit_code == 0

    assert runner.invoke(app, ["add", "High school assignment", "--priority", "low"]).exit_code == 0

    result = runner.invoke(app, ["search", "high"])

    assert result.exit_code == 0
    assert "High school assignment" in result.output
    assert "Buy groceries" not in result.output


def test_search_rejects_corrupted_csv_without_changing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    path = Path("storage_tasks/tasks.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "title,priority,due_date,status\nValid task,high,,pending\nbroken row\n",
        encoding="utf-8",
    )

    original_contents = path.read_bytes()

    result = runner.invoke(app, ["search", "Valid"])

    assert result.exit_code == 1
    assert "could not read" in result.stderr
    assert "Invalid CSV row 3" in result.stderr
    assert "Traceback" not in result.output
    assert path.read_bytes() == original_contents


def test_search_finds_matches_and_preserves_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["add", "Study Python"]).exit_code == 0
    assert runner.invoke(app, ["add", "Buy groceries"]).exit_code == 0
    assert runner.invoke(app, ["add", "Study Finance"]).exit_code == 0

    path = Path("storage_tasks/tasks.csv")
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["search", " STUDY "])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] Study Python - medium",
        "2. [PENDING] Study Finance - medium",
    ]
    assert path.read_bytes() == original_contents


def test_search_with_no_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["add", "Study Python"]).exit_code == 0

    result = runner.invoke(app, ["search", "exercise"])

    assert result.exit_code == 0
    assert "No matching tasks found." in result.output


def test_search_without_saved_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["search", "Study"])

    assert result.exit_code == 0
    assert "No tasks found." in result.output
    assert not Path("storage_tasks/tasks.csv").exists()


def test_search_rejects_blank_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["search", "   "])

    assert result.exit_code == 1
    assert "Search keyword cannot be empty." in result.stderr
    assert not Path("storage_tasks/tasks.csv").exists()


@pytest.mark.parametrize("command", ["delete", "edit"])
@pytest.mark.parametrize(
    ("selection", "expected_message"),
    [
        ("abc\n", "Invalid task number."),
        ("\n", "Invalid task number."),
        ("0\n", "Task number does not exist."),
        ("-1\n", "Task number does not exist."),
        ("99\n", "Task number does not exist."),
        ("", None),
    ],
)
def test_invalid_task_selection_preserves_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    selection: str,
    expected_message: str | None,
) -> None:
    monkeypatch.chdir(tmp_path)

    setup = runner.invoke(app, ["add", "Original task"])
    assert setup.exit_code == 0

    path = Path("storage_tasks/tasks.csv")
    original_contents = path.read_bytes()

    arguments = ["delete"] if command == "delete" else ["edit", "--title", "Updated"]

    result = runner.invoke(app, arguments, input=selection)

    assert result.exit_code != 0
    assert path.read_bytes() == original_contents

    if expected_message is not None:
        assert expected_message in result.output


def test_done_completes_task_and_saves_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["add", "Study Python"]).exit_code == 0

    result = runner.invoke(app, ["done"], input="1\n")

    assert result.exit_code == 0
    assert "completed Study Python" in result.output

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))
    assert saved_tasks[0].status == "completed"


def test_done_without_pending_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["add", "Study Python"]).exit_code == 0
    assert runner.invoke(app, ["done"], input="1\n").exit_code == 0

    result = runner.invoke(app, ["done"])

    assert result.exit_code == 1
    assert "No pending tasks found." in result.stderr


@pytest.mark.parametrize("selection", ["0\n", "-1\n", "99\n", "abc\n"])
def test_done_invalid_selection_preserves_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selection: str,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["add", "Study Python"]).exit_code == 0

    path = Path("storage_tasks/tasks.csv")
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["done"], input=selection)

    assert result.exit_code == 1
    assert path.read_bytes() == original_contents


def test_done_completes_displayed_task_without_changing_csv_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["add", "Buy groceries", "--priority", "low"]).exit_code == 0
    assert runner.invoke(app, ["add", "Study Python", "--priority", "high"]).exit_code == 0
    assert runner.invoke(app, ["add", "Study Finance", "--priority", "medium"]).exit_code == 0

    result = runner.invoke(app, ["done"], input="1\n")

    assert result.exit_code == 0
    assert "1. [PENDING] Study Python - high" in result.output
    assert "completed Study Python" in result.output

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))

    assert saved_tasks == [
        Task("Buy groceries", "low", "", "pending"),
        Task("Study Python", "high", "", "completed"),
        Task("Study Finance", "medium", "", "pending"),
    ]


def test_done_only_displays_pending_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    path = Path("storage_tasks/tasks.csv")

    write_tasks(
        path,
        [
            Task("Completed task", "high", "", "completed"),
            Task("Pending task", "low", "", "pending"),
        ],
    )

    result = runner.invoke(app, ["done"], input="1\n")

    assert result.exit_code == 0
    assert "Completed task" not in result.output
    assert "1. [PENDING] Pending task - low" in result.output
    assert "completed Pending task" in result.output

    assert read_tasks(path) == [
        Task("Completed task", "high", "", "completed"),
        Task("Pending task", "low", "", "completed"),
    ]


def test_reopen_changes_status_and_saves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["add", "Study Python"]).exit_code == 0
    assert runner.invoke(app, ["done"], input="1\n").exit_code == 0

    result = runner.invoke(app, ["reopen"], input="1\n")

    assert result.exit_code == 0
    assert "reopened Study Python" in result.output

    saved_tasks = read_tasks(Path("storage_tasks/tasks.csv"))
    assert saved_tasks[0].status == "pending"


def test_reopen_without_completed_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["add", "Study Python"]).exit_code == 0

    result = runner.invoke(app, ["reopen"])

    assert result.exit_code == 1
    assert "No completed tasks found." in result.stderr


@pytest.mark.parametrize("selection", ["0\n", "-1\n", "99\n", "abc\n"])
def test_reopen_invalid_selection_preserves_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selection: str,
) -> None:
    monkeypatch.chdir(tmp_path)

    path = Path("storage_tasks/tasks.csv")
    write_tasks(path, [Task("Study Python", "high", "", "completed")])

    original_contents = path.read_bytes()

    result = runner.invoke(app, ["reopen"], input=selection)

    assert result.exit_code == 1
    assert path.read_bytes() == original_contents


def test_reopen_respects_displayed_order_and_preserves_csv_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    path = Path("storage_tasks/tasks.csv")

    write_tasks(
        path,
        [
            Task("Buy groceries", "low", "", "completed"),
            Task("Study Python", "high", "", "completed"),
            Task("Study Finance", "medium", "", "pending"),
        ],
    )

    result = runner.invoke(app, ["reopen"], input="1\n")

    assert result.exit_code == 0
    assert "1. [COMPLETED] Study Python - high" in result.output
    assert "reopened Study Python" in result.output

    assert read_tasks(path) == [
        Task("Buy groceries", "low", "", "completed"),
        Task("Study Python", "high", "", "pending"),
        Task("Study Finance", "medium", "", "pending"),
    ]


def test_reopen_only_displays_completed_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    path = Path("storage_tasks/tasks.csv")

    write_tasks(
        path,
        [
            Task("Pending task", "high", "", "pending"),
            Task("Completed task", "low", "", "completed"),
        ],
    )

    result = runner.invoke(app, ["reopen"], input="1\n")

    assert result.exit_code == 0
    assert "[PENDING] Pending task" not in result.output
    assert "1. [COMPLETED] Completed task - low" in result.output
    assert "reopened Completed task" in result.output

    assert read_tasks(path) == [
        Task("Pending task", "high", "", "pending"),
        Task("Completed task", "low", "", "pending"),
    ]


def test_add_rejects_duplicate_of_completed_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [Task("Study Python", "high", "", "completed")],
    )

    result = runner.invoke(
        app,
        ["add", "Study Python", "--priority", "high"],
    )

    assert result.exit_code == 1
    assert "Task already exists." in result.stderr

    saved_tasks = read_tasks(path)
    assert saved_tasks == [
        Task("Study Python", "high", "", "completed"),
    ]


def test_edit_rejects_duplicate_with_different_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    path = Path("storage_tasks/tasks.csv")
    original_tasks = [
        Task("Study Python", "high", "", "completed"),
        Task("Study Finance", "medium", "", "pending"),
    ]
    write_tasks(path, original_tasks)

    result = runner.invoke(
        app,
        ["edit", "--title", "Study Python", "--priority", "high"],
        input="2\n",
    )

    assert result.exit_code == 1
    assert "Task already exists." in result.stderr
    assert read_tasks(path) == original_tasks


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (
            "pending",
            [
                "1. [PENDING] Pending high - high",
                "2. [PENDING] Pending low - low",
            ],
        ),
        ("completed", ["1. [COMPLETED] Completed high - high"]),
        (
            "all",
            [
                "1. [COMPLETED] Completed high - high",
                "2. [PENDING] Pending high - high",
                "3. [PENDING] Pending low - low",
            ],
        ),
    ],
)
def test_list_filters_by_status_without_changing_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    expected: list[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Pending low", "low"),
            Task("Completed high", "high", "", "completed"),
            Task("Pending high", "high"),
        ],
    )
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["list", "--status", status])

    assert result.exit_code == 0
    assert result.output.splitlines() == expected
    assert path.read_bytes() == original_contents

    if status == "all":
        assert runner.invoke(app, ["list"]).output == result.output


def test_list_reports_when_no_tasks_match_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    path = Path("storage_tasks/tasks.csv")
    write_tasks(path, [Task("Pending task", "high")])
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["list", "--status", "completed"])

    assert result.exit_code == 0
    assert "No completed tasks found." in result.output
    assert path.read_bytes() == original_contents


def test_list_rejects_invalid_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["list", "--status", "waiting"])

    assert result.exit_code == 1
    assert "Status must be one of: pending, completed, all, overdue." in result.stderr


def test_list_overdue_shows_only_pending_past_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 16))

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Past", "high", "2026-11-15"),
            Task("Today", "high", "2026-11-16"),
            Task("Completed past", "high", "2026-11-14", "completed"),
            Task("No date", "low"),
        ],
    )
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["list", "--status", "overdue"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] [OVERDUE] Past - high - due 2026-11-15",
    ]
    assert path.read_bytes() == original_contents


def test_list_combines_status_priority_and_date_sort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 1, 1))
    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Late high", "high", "2026-12-01"),
            Task("No date high", "high"),
            Task("Early high", "high", "2026-10-01"),
            Task("Early medium", "medium", "2026-09-01"),
            Task("Completed high", "high", "2026-08-01", "completed"),
        ],
    )
    original_contents = path.read_bytes()

    result = runner.invoke(
        app,
        ["list", "--status", "pending", "--priority", "high", "--sort-by", "date"],
    )

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] Early high - high - due 2026-10-01",
        "2. [PENDING] Late high - high - due 2026-12-01",
        "3. [PENDING] No date high - high",
    ]
    assert path.read_bytes() == original_contents


def test_list_combines_overdue_and_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 16))
    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Past low", "low", "2026-11-15"),
            Task("Past high", "high", "2026-11-14"),
            Task("Completed high", "high", "2026-11-13", "completed"),
        ],
    )

    result = runner.invoke(
        app,
        ["list", "--status", "overdue", "--priority", "high", "--sort-by", "date"],
    )

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] [OVERDUE] Past high - high - due 2026-11-14",
    ]


def test_list_rejects_invalid_priority_filter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["list", "--priority", "urgent"])

    assert result.exit_code == 1
    assert "Priority filter must be one of: high, medium, low, all." in result.stderr


def test_list_highlights_overdue_without_filter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 16))

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Late", "high", "2026-11-15"),
            Task("Due today", "medium", "2026-11-16"),
            Task("Completed late", "low", "2026-11-14", "completed"),
        ],
    )
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] [OVERDUE] Late - high - due 2026-11-15",
        "2. [PENDING] Due today - medium - due 2026-11-16",
        "3. [COMPLETED] Completed late - low - due 2026-11-14",
    ]
    assert path.read_bytes() == original_contents


def test_today_shows_overdue_and_due_today_without_changing_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 17))

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Due today", "medium", "2026-11-17"),
            Task("Future", "high", "2026-11-18"),
            Task("Overdue", "low", "2026-11-15"),
            Task("Completed overdue", "high", "2026-11-10", "completed"),
            Task("No date", "medium"),
        ],
    )
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] [OVERDUE] Overdue - low - due 2026-11-15",
        "2. [PENDING] [DUE TODAY] Due today - medium - due 2026-11-17",
    ]
    assert path.read_bytes() == original_contents


def test_today_handles_no_matching_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 17))

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Future", "high", "2026-11-20"),
            Task("Completed overdue", "medium", "2026-11-15", "completed"),
            Task("No date", "low"),
        ],
    )

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 0
    assert result.output.strip() == "No tasks due today or overdue."


def test_today_handles_missing_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 0
    assert result.output.strip() == "No tasks due today or overdue."


def test_due_soon_shows_upcoming_tasks_without_changing_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 17))

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Day 7", "low", "2026-11-24"),
            Task("Overdue", "high", "2026-11-16"),
            Task("Day 1", "medium", "2026-11-18"),
            Task("Today", "high", "2026-11-17"),
            Task("Day 8", "high", "2026-11-25"),
            Task("Day 3", "high", "2026-11-20"),
            Task("Completed", "high", "2026-11-19", "completed"),
            Task("No date", "low"),
        ],
    )
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["due-soon"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "1. [PENDING] Day 1 - medium - due 2026-11-18",
        "2. [PENDING] Day 3 - high - due 2026-11-20",
        "3. [PENDING] Day 7 - low - due 2026-11-24",
    ]
    assert path.read_bytes() == original_contents


def test_due_soon_handles_no_matching_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 17))

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Today", "high", "2026-11-17"),
            Task("Day 8", "medium", "2026-11-25"),
            Task("Completed", "low", "2026-11-18", "completed"),
        ],
    )

    result = runner.invoke(app, ["due-soon"])

    assert result.exit_code == 0
    assert result.output.strip() == "No tasks due in the next seven days."


def test_due_soon_handles_missing_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["due-soon"])

    assert result.exit_code == 0
    assert result.output.strip() == "No tasks due in the next seven days."


def test_summary_displays_statistics_without_changing_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 17))

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Overdue high", "high", "2026-11-16"),
            Task("Today medium", "medium", "2026-11-17"),
            Task("Future low", "low", "2026-11-20"),
            Task("Completed high", "high", "2026-11-15", "completed"),
            Task("Completed medium", "medium", "", "completed"),
        ],
    )
    original_contents = path.read_bytes()

    result = runner.invoke(app, ["summary"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "Task Summary",
        "------------",
        "Total tasks: 5",
        "Pending: 3",
        "Completed: 2",
        "Overdue: 1",
        "Completion rate: 40.0%",
        "",
        "Tasks by priority:",
        "High: 2",
        "Medium: 2",
        "Low: 1",
    ]
    assert path.read_bytes() == original_contents


def test_summary_handles_empty_task_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    path = Path("storage_tasks/tasks.csv")
    write_tasks(path, [])

    result = runner.invoke(app, ["summary"])

    assert result.exit_code == 0
    assert "Total tasks: 0" in result.output
    assert "Pending: 0" in result.output
    assert "Completed: 0" in result.output
    assert "Overdue: 0" in result.output
    assert "Completion rate: 0.0%" in result.output
    assert "High: 0" in result.output
    assert "Medium: 0" in result.output
    assert "Low: 0" in result.output


def test_summary_handles_missing_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["summary"])

    assert result.exit_code == 0
    assert "Total tasks: 0" in result.output
    assert "Completion rate: 0.0%" in result.output


def test_custom_data_files_keep_tasks_separate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    university_file = tmp_path / "university.csv"
    personal_file = tmp_path / "personal.csv"

    result_university = runner.invoke(
        app,
        ["--data-file", str(university_file), "add", "Study Python"],
    )

    result_personal = runner.invoke(
        app,
        ["--data-file", str(personal_file), "add", "Buy groceries"],
    )

    assert result_university.exit_code == 0
    assert result_personal.exit_code == 0

    university_tasks = read_tasks(university_file)
    personal_tasks = read_tasks(personal_file)

    assert [task.title for task in university_tasks] == ["Study Python"]
    assert [task.title for task in personal_tasks] == ["Buy groceries"]

    university_list = runner.invoke(
        app,
        ["--data-file", str(university_file), "list"],
    )

    personal_list = runner.invoke(
        app,
        ["--data-file", str(personal_file), "list"],
    )

    assert university_list.exit_code == 0
    assert personal_list.exit_code == 0

    assert "Study Python" in university_list.output
    assert "Buy groceries" not in university_list.output

    assert "Buy groceries" in personal_list.output
    assert "Study Python" not in personal_list.output

    assert not Path("storage_tasks/tasks.csv").exists()


def test_custom_data_file_relative_path_with_spaces(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    relative_file = Path("my task folders") / "semester tasks.csv"

    result = runner.invoke(
        app,
        ["--data-file", str(relative_file), "add", "Prepare exam"],
    )

    assert result.exit_code == 0
    assert relative_file.exists()

    saved_tasks = read_tasks(relative_file)
    assert [task.title for task in saved_tasks] == ["Prepare exam"]

    list_result = runner.invoke(
        app,
        ["--data-file", str(relative_file), "list"],
    )

    assert list_result.exit_code == 0
    assert "Prepare exam" in list_result.output

    assert not Path("storage_tasks/tasks.csv").exists()


def test_default_data_file_still_works(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    default_file = Path("storage_tasks/tasks.csv")

    result = runner.invoke(
        app,
        ["add", "Study Python"],
    )

    assert result.exit_code == 0
    assert default_file.exists()

    saved_tasks = read_tasks(default_file)
    assert len(saved_tasks) == 1
    assert saved_tasks[0].title == "Study Python"

    list_result = runner.invoke(app, ["list"])

    assert list_result.exit_code == 0
    assert "Study Python" in list_result.output


def test_custom_data_file_done_and_reopen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    university_file = tmp_path / "university.csv"
    personal_file = tmp_path / "personal.csv"

    # Create one task in each file
    assert (
        runner.invoke(
            app,
            ["--data-file", str(university_file), "add", "Study Python"],
        ).exit_code
        == 0
    )

    assert (
        runner.invoke(
            app,
            ["--data-file", str(personal_file), "add", "Buy groceries"],
        ).exit_code
        == 0
    )

    original_personal_csv = personal_file.read_bytes()

    # Complete the university task
    result_done = runner.invoke(
        app,
        ["--data-file", str(university_file), "done"],
        input="1\n",
    )

    assert result_done.exit_code == 0
    assert read_tasks(university_file)[0].status == "completed"
    assert personal_file.read_bytes() == original_personal_csv

    # Reopen the university task
    result_reopen = runner.invoke(
        app,
        ["--data-file", str(university_file), "reopen"],
        input="1\n",
    )

    assert result_reopen.exit_code == 0
    assert read_tasks(university_file)[0].status == "pending"
    assert personal_file.read_bytes() == original_personal_csv


def test_custom_data_file_delete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    university_file = tmp_path / "university.csv"
    personal_file = tmp_path / "personal.csv"

    assert (
        runner.invoke(
            app,
            ["--data-file", str(university_file), "add", "Study Finance", "--priority", "low"],
        ).exit_code
        == 0
    )

    assert (
        runner.invoke(
            app,
            ["--data-file", str(university_file), "add", "Study Python", "--priority", "high"],
        ).exit_code
        == 0
    )

    assert (
        runner.invoke(
            app,
            ["--data-file", str(personal_file), "add", "Buy groceries"],
        ).exit_code
        == 0
    )

    original_personal_csv = personal_file.read_bytes()

    result = runner.invoke(
        app,
        ["--data-file", str(university_file), "delete"],
        input="1\n",
    )

    assert result.exit_code == 0
    assert "deleted Study Python" in result.output

    saved_tasks = read_tasks(university_file)
    assert [task.title for task in saved_tasks] == ["Study Finance"]

    assert personal_file.read_bytes() == original_personal_csv


def test_custom_data_file_edit_search_and_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    custom_file = tmp_path / "university.csv"

    result = runner.invoke(
        app,
        ["--data-file", str(custom_file), "add", "Study Python"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        app,
        ["--data-file", str(custom_file), "edit", "--priority", "high"],
        input="1\n",
    )
    assert result.exit_code == 0
    assert read_tasks(custom_file)[0].priority == "high"

    result = runner.invoke(
        app,
        ["--data-file", str(custom_file), "search", "Python"],
    )
    assert result.exit_code == 0
    assert "Study Python" in result.output

    result = runner.invoke(
        app,
        ["--data-file", str(custom_file), "summary"],
    )
    assert result.exit_code == 0
    assert "Total tasks: 1" in result.output
    assert "High: 1" in result.output


def test_weekly_review_displays_report_without_changing_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "current_date", lambda: date(2026, 11, 17))

    path = Path("storage_tasks/tasks.csv")
    write_tasks(
        path,
        [
            Task("Overdue task", "high", "2026-11-16"),
            Task("Upcoming task", "medium", "2026-11-20"),
            Task("Completed task", "low", "2026-11-15", "completed"),
            Task("Outside the week", "high", "2026-11-25"),
        ],
    )

    original_contents = path.read_bytes()

    result = runner.invoke(app, ["weekly-review"])

    assert result.exit_code == 0
    assert "WEEKLY REVIEW" in result.output
    assert "OVERDUE TASKS (1)" in result.output
    assert "Overdue task" in result.output
    assert "UPCOMING - NEXT 7 DAYS (1)" in result.output
    assert "Upcoming task" in result.output
    assert "CURRENTLY COMPLETED: 1 TASKS" in result.output
    assert "Outside the week" not in result.output

    assert path.read_bytes() == original_contents
