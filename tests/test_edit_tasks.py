import pytest

from task_manager.edit_tasks import edit_task
from task_manager.models import (
    EmptyTitleError,
    InvalidDueDate,
    InvalidNumberTasks,
    InvalidPriority,
    Task,
)


def test_edit_task_changes_title() -> None:
    original_task = Task("Study Software", "high", "2026-11-05")
    tasks = [original_task]

    edited_task, updated_tasks = edit_task(tasks, 1, title="Study Git")

    expected_task = Task("Study Git", "high", "2026-11-05")

    assert edited_task == expected_task
    assert updated_tasks == [expected_task]
    assert tasks == [original_task]


def test_edit_task_changes_priority() -> None:
    original_task = Task("Study Software", "low", "2026-11-05")
    tasks = [original_task]

    edited_task, updated_tasks = edit_task(tasks, 1, priority="high")

    expected_task = Task("Study Software", "high", "2026-11-05")

    assert edited_task == expected_task
    assert updated_tasks == [expected_task]
    assert tasks == [original_task]


def test_edit_task_changes_due_date() -> None:
    original_task = Task("Study Software", "high", "2026-11-05")
    tasks = [original_task]

    edited_task, updated_tasks = edit_task(tasks, 1, due_date="2026-11-10")

    expected_task = Task("Study Software", "high", "2026-11-10")

    assert edited_task == expected_task
    assert updated_tasks == [expected_task]
    assert tasks == [original_task]


def test_edit_task_clears_due_date() -> None:
    original_task = Task("Study Software", "high", "2026-11-05")
    tasks = [original_task]

    edited_task, updated_tasks = edit_task(tasks, 1, due_date="")

    expected_task = Task("Study Software", "high", "")

    assert edited_task == expected_task
    assert updated_tasks == [expected_task]
    assert tasks == [original_task]


def test_edit_task_without_changes_keeps_values() -> None:
    original_task = Task("Study Software", "high", "2026-11-05")
    tasks = [original_task]

    edited_task, updated_tasks = edit_task(tasks, 1)

    assert edited_task == original_task
    assert updated_tasks == [original_task]
    assert tasks == [original_task]
    assert updated_tasks is not tasks


def test_edit_task_changes_all_fields_of_selected_task() -> None:
    first_task = Task("Buy groceries", "low", "")
    second_task = Task("Study Software", "medium", "2026-11-05")
    tasks = [first_task, second_task]

    edited_task, updated_tasks = edit_task(
        tasks,
        2,
        title="Study Git",
        priority="high",
        due_date="2026-11-10",
    )

    expected_task = Task("Study Git", "high", "2026-11-10")

    assert edited_task == expected_task
    assert updated_tasks == [first_task, expected_task]
    assert tasks == [first_task, second_task]


@pytest.mark.parametrize("task_number", [-1, 0, 2])
def test_edit_task_rejects_invalid_number(task_number: int) -> None:
    original_task = Task("Study Software", "high", "2026-11-05")
    tasks = [original_task]

    with pytest.raises(InvalidNumberTasks, match="Task number does not exist"):
        edit_task(tasks, task_number, title="Study Git")

    assert tasks == [original_task]


def test_edit_task_rejects_empty_title() -> None:
    original_task = Task("Study Software", "high", "2026-11-05")
    tasks = [original_task]

    with pytest.raises(EmptyTitleError, match="Title cannot be empty"):
        edit_task(tasks, 1, title="   ")

    assert tasks == [original_task]


def test_edit_task_rejects_invalid_priority() -> None:
    original_task = Task("Study Software", "high", "2026-11-05")
    tasks = [original_task]

    with pytest.raises(InvalidPriority, match="Priority must be one of"):
        edit_task(tasks, 1, priority="urgent")

    assert tasks == [original_task]


def test_edit_task_rejects_invalid_due_date() -> None:
    original_task = Task("Study Software", "high", "2026-11-05")
    tasks = [original_task]

    with pytest.raises(InvalidDueDate, match="Due date must use YYYY-MM-DD"):
        edit_task(tasks, 1, due_date="10-11-2026")

    assert tasks == [original_task]


def test_edit_task_normalizes_new_values() -> None:
    original_task = Task("Study Software", "low", "")
    tasks = [original_task]

    edited_task, updated_tasks = edit_task(
        tasks,
        1,
        title="  Study Git  ",
        priority=" HIGH ",
        due_date=" 2026-11-10 ",
    )

    expected_task = Task("Study Git", "high", "2026-11-10")

    assert edited_task == expected_task
    assert updated_tasks == [expected_task]
    assert tasks == [original_task]


def test_edit_task_rejects_empty_list() -> None:
    tasks: list[Task] = []

    with pytest.raises(InvalidNumberTasks, match="Task number does not exist"):
        edit_task(tasks, 1, title="Study Git")

    assert tasks == []
