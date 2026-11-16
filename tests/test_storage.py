from pathlib import Path

import pytest

from task_manager.models import Task
from task_manager.storage import append_task, delete_task, read_tasks, write_tasks


def test_append_task_creates_csv_and_saves_task(tmp_path: Path) -> None:
    path = tmp_path / "storage_tasks" / "tasks.csv"
    task = Task("Study Finance", "high", "2026-10-20")

    append_task(path, task)

    assert path.exists()
    assert read_tasks(path) == [task]


def test_append_task_keeps_existing_tasks(tmp_path: Path) -> None:
    path = tmp_path / "storage_tasks" / "tasks.csv"

    first = Task("First task", "high")
    second = Task("Second task", "low")

    append_task(path, first)
    append_task(path, second)

    assert read_tasks(path) == [first, second]


def test_read_tasks_rejects_broken_row_without_changing_file(tmp_path: Path) -> None:
    path = tmp_path / "tasks.csv"
    path.write_text(
        "title,priority,due_date\n"
        "Study Finance,high,2026-10-20\n"
        "broken row\n"
        "Buy groceries,medium,\n",
        encoding="utf-8",
    )
    original_contents = path.read_bytes()

    with pytest.raises(ValueError, match="Invalid CSV row 3"):
        read_tasks(path)

    assert path.read_bytes() == original_contents


@pytest.mark.parametrize(
    ("bad_row", "message"),
    [
        ("Study,urgent,2026-11-20", "Priority must be one of"),
        ("Study,high,2026-02-30", "Due date must use YYYY-MM-DD."),
        ("   ,high,2026-11-20", "Title cannot be empty."),
    ],
)
def test_read_tasks_rejects_invalid_values_without_changing_file(
    tmp_path: Path,
    bad_row: str,
    message: str,
) -> None:
    path = tmp_path / "tasks.csv"
    path.write_text(
        f"title,priority,due_date\nValid task,medium,\n{bad_row}\n",
        encoding="utf-8",
    )
    original_contents = path.read_bytes()

    with pytest.raises(ValueError) as error:
        read_tasks(path)

    assert "Invalid CSV row 3:" in str(error.value)
    assert message in str(error.value)
    assert path.read_bytes() == original_contents


def test_write_tasks_replaces_previous_contents(tmp_path: Path) -> None:
    path = tmp_path / "storage_tasks" / "tasks.csv"

    append_task(path, Task("Old task", "low"))

    new_tasks = [Task("New task", "high", "2026-10-20")]
    write_tasks(path, new_tasks)

    assert read_tasks(path) == new_tasks


def test_delete_task_removes_selected_task(tmp_path: Path) -> None:
    path = tmp_path / "tasks.csv"

    first = Task("Study", "high")
    second = Task("Exercise", "medium")
    third = Task("Shopping", "low")
    write_tasks(path, [first, second, third])

    delete_task(path, 2)

    assert read_tasks(path) == [first, third]


def test_delete_only_task_leaves_no_tasks(tmp_path: Path) -> None:
    path = tmp_path / "tasks.csv"

    task = Task("Study", "high")
    write_tasks(path, [task])

    delete_task(path, 1)

    assert read_tasks(path) == []


def test_delete_does_not_overwrite_malformed_file(tmp_path: Path) -> None:
    path = tmp_path / "tasks.csv"
    path.write_text(
        "title,priority,due_date\nValid task,high,\nbroken row\n",
        encoding="utf-8",
    )
    original_contents = path.read_bytes()

    with pytest.raises(ValueError, match="Invalid CSV row 3"):
        delete_task(path, 1)

    assert path.read_bytes() == original_contents


def test_read_tasks_rejects_invalid_csv_header(tmp_path: Path) -> None:
    csv_file = tmp_path / "tasks.csv"
    csv_file.write_text(
        "name,priority,due_date\nBuy groceries,high,2026-11-20\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid CSV header"):
        read_tasks(csv_file)


def test_read_tasks_accepts_valid_csv_header(tmp_path: Path) -> None:
    csv_file = tmp_path / "tasks.csv"
    csv_file.write_text(
        "title,priority,due_date\nBuy groceries,high,2026-11-20\n",
        encoding="utf-8",
    )

    tasks = read_tasks(csv_file)

    assert tasks == [Task("Buy groceries", "high", "2026-11-20")]


@pytest.mark.parametrize(
    "header",
    [
        "title,priority",
        "priority,title,due_date",
        "title,priority,due_date,status",
        "",
    ],
)
def test_read_tasks_rejects_invalid_header_formats(
    tmp_path: Path,
    header: str,
) -> None:
    csv_file = tmp_path / "tasks.csv"
    csv_file.write_text(
        header + "\nBuy groceries,high,2026-11-20\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid CSV header"):
        read_tasks(csv_file)


def test_read_tasks_accepts_header_without_tasks(tmp_path: Path) -> None:
    csv_file = tmp_path / "tasks.csv"
    csv_file.write_text(
        "title,priority,due_date\n",
        encoding="utf-8",
    )

    tasks = read_tasks(csv_file)

    assert tasks == []


def test_read_tasks_accepts_special_characters_in_titles(tmp_path: Path) -> None:
    path = tmp_path / "tasks.csv"
    path.write_text(
        "title,priority,due_date\n"
        '"Buy, milk",medium,\n'
        '"Say ""hello""",high,\n'
        "Cafè ☕,low,2026-11-20\n",
        encoding="utf-8",
    )

    assert read_tasks(path) == [
        Task("Buy, milk", "medium", ""),
        Task('Say "hello"', "high", ""),
        Task("Cafè ☕", "low", "2026-11-20"),
    ]


def test_read_tasks_rejects_invalid_csv_syntax_without_changing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "tasks.csv"
    path.write_text(
        'title,priority,due_date\n"Unclosed title,high,2026-10-20\n',
        encoding="utf-8",
    )
    original_contents = path.read_bytes()

    with pytest.raises(ValueError, match="Invalid CSV syntax"):
        read_tasks(path)

    assert path.read_bytes() == original_contents


def test_write_tasks_raises_error_when_file_cannot_be_opened(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "tasks.csv"
    tasks = [Task("Study Finance", "high")]

    original_open = Path.open

    def failing_open(self: Path, *args: object, **kwargs: object):
        if self == path and args and args[0] == "w":
            raise PermissionError("Permission denied")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)

    with pytest.raises(PermissionError, match="Permission denied"):
        write_tasks(path, tasks)
