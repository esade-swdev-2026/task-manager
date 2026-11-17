from datetime import date

import pytest

from task_manager.models import (
    EmptyTitleError,
    InvalidDueDate,
    InvalidNumberTasks,
    InvalidPriority,
    InvalidStatus,
    Task,
)
from task_manager.tasks import (
    add_task,
    complete_task,
    count_tasks_by_priority,
    create_task,
    delete_task,
    filter_overdue_tasks,
    filter_tasks_by_priority,
    filter_tasks_by_status,
    get_original_task_number,
    is_duplicate,
    is_overdue,
    remove_duplicate_tasks,
    reopen_task,
    search_tasks,
    sort_tasks_by_due_date,
    sort_tasks_by_priority,
)

GROCERIES = Task("Buy groceries", "medium", "2026-11-17")
PRESENT = Task("Buy Present", "low", "2027-12-02")
FINANCE = Task("Study Finance", "high", "2026-12-01")
GYM = Task("Go to the Gym", "low", "2026-11-04")
DOCTOR = Task("Doctor Appointment", "high", "2026-10-31")
EARLY = Task("Early task", "medium", "2026-10-01")
LATE = Task("Late task", "medium", "2026-12-01")
NO_DATE = Task("No date task", "medium")


def test_create_task_normalizes_values() -> None:
    result = create_task("  Study Finance  ", "HIGH", "2026-12-01")

    assert result == FINANCE


def test_create_task_rejects_empty_title() -> None:
    with pytest.raises(EmptyTitleError, match="Title cannot be empty"):
        create_task("   ")


def test_create_task_rejects_invalid_priority() -> None:
    with pytest.raises(InvalidPriority, match="Priority must be one of"):
        create_task("Study Finance", "urgent")


def test_create_task_rejects_invalid_due_date() -> None:
    with pytest.raises(InvalidDueDate, match="Due date must use YYYY-MM-DD"):
        create_task("Study Finance", due_date="01-12-2026")


def test_add_task() -> None:
    tasks: list[Task] = []

    task = add_task(tasks, "Study Finance", "high")

    assert task == Task("Study Finance", "high")
    assert tasks == [task]


def test_count_empty_list_of_tasks() -> None:
    assert count_tasks_by_priority([]) == {"high": 0, "medium": 0, "low": 0}


def test_count_different_priorities() -> None:
    tasks = [FINANCE, GROCERIES, GYM, PRESENT]

    assert count_tasks_by_priority(tasks) == {"high": 1, "medium": 1, "low": 2}


def test_count_only_high_priority() -> None:
    result = count_tasks_by_priority([FINANCE, DOCTOR])

    assert result == {"high": 2, "medium": 0, "low": 0}


def test_sort_by_priority() -> None:
    result = sort_tasks_by_priority([GYM, GROCERIES, FINANCE])

    assert result == [FINANCE, GROCERIES, GYM]


def test_sort_by_priority_empty() -> None:
    assert sort_tasks_by_priority([]) == []


def test_sort_by_priority_does_not_modify_original() -> None:
    tasks = [GYM, FINANCE]

    sort_tasks_by_priority(tasks)

    assert tasks == [GYM, FINANCE]


def test_sort_by_due_date_earliest_first() -> None:
    assert sort_tasks_by_due_date([LATE, EARLY]) == [EARLY, LATE]


def test_sort_by_due_date_puts_no_date_last() -> None:
    result = sort_tasks_by_due_date([NO_DATE, LATE, EARLY])

    assert result == [EARLY, LATE, NO_DATE]


def test_sort_by_due_date_empty() -> None:
    assert sort_tasks_by_due_date([]) == []


def test_sort_by_due_date_between_years() -> None:
    last_year_task = Task("Old", "low", "2025-12-31")
    this_year_task = Task("New", "low", "2026-01-01")

    result = sort_tasks_by_due_date([this_year_task, last_year_task])

    assert result == [last_year_task, this_year_task]


def test_sort_by_due_date_keeps_tie_order() -> None:
    first = Task("First", "low", "2026-10-01")
    second = Task("Second", "high", "2026-10-01")

    assert sort_tasks_by_due_date([first, second]) == [first, second]


def test_sort_by_due_date_does_not_modify_original() -> None:
    tasks = [LATE, EARLY]

    sort_tasks_by_due_date(tasks)

    assert tasks == [LATE, EARLY]


def test_remove_duplicates_empty() -> None:
    assert remove_duplicate_tasks([]) == []


def test_no_duplicates_remains_unchanged() -> None:
    tasks = [FINANCE, GYM, GROCERIES]

    assert remove_duplicate_tasks(tasks) == tasks


def test_remove_exact_duplicate() -> None:
    copy = Task("Study Finance", "high", "2026-12-01")

    assert remove_duplicate_tasks([FINANCE, copy]) == [FINANCE]


def test_remove_many_duplicates() -> None:
    assert remove_duplicate_tasks([GYM, GYM, GYM]) == [GYM]


def test_remove_duplicates_keeps_order() -> None:
    result = remove_duplicate_tasks([GYM, FINANCE, GYM, GROCERIES, FINANCE])

    assert result == [GYM, FINANCE, GROCERIES]


def test_same_name_different_priority_is_kept() -> None:
    low_task = Task("Eat Lunch", "low")
    high_task = Task("Eat Lunch", "high")

    assert remove_duplicate_tasks([low_task, high_task]) == [low_task, high_task]


def test_same_name_different_date_is_kept() -> None:
    first = Task("Same title", "low", "2026-10-01")
    second = Task("Same title", "low", "2026-10-02")

    assert remove_duplicate_tasks([first, second]) == [first, second]


def test_remove_duplicates_does_not_modify_original() -> None:
    tasks = [GYM, GYM]

    remove_duplicate_tasks(tasks)

    assert tasks == [GYM, GYM]


def test_exact_task_is_duplicate() -> None:
    assert is_duplicate(FINANCE, [FINANCE]) is True


def test_different_priority_is_not_duplicate() -> None:
    low_priority_task = Task("Study Finance", "low", "2026-12-01")

    assert is_duplicate(FINANCE, [low_priority_task]) is False


def test_different_date_is_not_duplicate() -> None:
    different_date = Task("Study Finance", "high", "2026-12-02")

    assert is_duplicate(FINANCE, [different_date]) is False


def test_delete_task_returns_deleted_and_remaining_tasks() -> None:
    tasks = [FINANCE, GROCERIES]

    deleted_task, remaining_tasks = delete_task(tasks, 1)

    assert deleted_task == FINANCE
    assert remaining_tasks == [GROCERIES]
    assert tasks == [FINANCE, GROCERIES]


def test_delete_task_rejects_zero() -> None:
    tasks = [FINANCE, GROCERIES]

    with pytest.raises(InvalidNumberTasks, match="Task number does not exist"):
        delete_task(tasks, 0)


def test_delete_task_rejects_number_too_large() -> None:
    tasks = [FINANCE, GROCERIES]

    with pytest.raises(InvalidNumberTasks, match="Task number does not exist"):
        delete_task(tasks, 3)


def test_search_tasks_by_keyword() -> None:
    tasks = [
        create_task("Study Python"),
        create_task("Buy groceries"),
        create_task("Study Finance"),
    ]

    result = search_tasks(tasks, "Study")

    assert len(result) == 2
    assert result[0].title == "Study Python"
    assert result[1].title == "Study Finance"


def test_search_tasks_case_insensitive() -> None:
    tasks = [
        create_task("Study Python"),
        create_task("Buy groceries"),
    ]

    result = search_tasks(tasks, "PYTHON")

    assert len(result) == 1
    assert result[0].title == "Study Python"


def test_search_tasks_no_matches() -> None:
    tasks = [
        create_task("Study Python"),
        create_task("Buy groceries"),
    ]

    result = search_tasks(tasks, "exercise")

    assert result == []


def test_search_tasks_empty_list() -> None:
    result = search_tasks([], "Python")

    assert result == []


def test_search_tasks_partial_keyword() -> None:
    tasks = [
        create_task("Study Python"),
        create_task("Buy groceries"),
    ]

    result = search_tasks(tasks, "yth")

    assert len(result) == 1
    assert result[0].title == "Study Python"


def test_get_original_task_number_preserves_storage_order() -> None:
    tasks = [
        Task("Low task", "low"),
        Task("High task", "high"),
        Task("Medium task", "medium"),
    ]

    displayed_tasks = sort_tasks_by_priority(tasks)

    assert get_original_task_number(tasks, displayed_tasks, 1) == 2
    assert get_original_task_number(tasks, displayed_tasks, 2) == 3
    assert get_original_task_number(tasks, displayed_tasks, 3) == 1


@pytest.mark.parametrize("task_number", [0, -1, 4])
def test_get_original_task_number_rejects_invalid_numbers(
    task_number: int,
) -> None:
    tasks = [
        Task("Low task", "low"),
        Task("High task", "high"),
        Task("Medium task", "medium"),
    ]

    displayed_tasks = sort_tasks_by_priority(tasks)

    with pytest.raises(InvalidNumberTasks, match="Task number does not exist."):
        get_original_task_number(tasks, displayed_tasks, task_number)


def test_get_original_task_number_handles_identical_tasks() -> None:
    first = Task("Same task", "high")
    second = Task("Same task", "high")

    tasks = [first, second]
    displayed_tasks = sort_tasks_by_priority(tasks)

    assert get_original_task_number(tasks, displayed_tasks, 2) == 2


def test_create_task_defaults_to_pending() -> None:
    task = create_task("Study Python", "high")

    assert task.status == "pending"


def test_create_task_with_completed_status() -> None:
    task = create_task("Study Python", "high", "", "COMPLETED")

    assert task.status == "completed"


def test_create_task_rejects_invalid_status() -> None:
    with pytest.raises(InvalidStatus):
        create_task("Study Python", "high", "", "banana")


def test_complete_task() -> None:
    tasks = [
        Task("Study Python", "high"),
        Task("Buy groceries", "low"),
    ]

    completed_task, updated_tasks = complete_task(tasks, 1)

    assert completed_task.status == "completed"
    assert updated_tasks[0].status == "completed"
    assert updated_tasks[1].status == "pending"
    assert tasks[0].status == "pending"


def test_complete_task_rejects_already_completed() -> None:
    tasks = [Task("Study Python", "high", "", "completed")]

    with pytest.raises(ValueError, match="Task is already completed."):
        complete_task(tasks, 1)


@pytest.mark.parametrize("task_number", [0, -1, 2])
def test_complete_task_rejects_invalid_number(task_number: int) -> None:
    tasks = [Task("Study Python", "high")]

    with pytest.raises(InvalidNumberTasks):
        complete_task(tasks, task_number)


def test_reopen_task() -> None:
    tasks = [
        Task("Study Python", "high", "", "completed"),
        Task("Buy groceries", "low", "", "pending"),
    ]

    reopened_task, updated_tasks = reopen_task(tasks, 1)

    assert reopened_task.status == "pending"
    assert updated_tasks[0].status == "pending"
    assert updated_tasks[1].status == "pending"
    assert tasks[0].status == "completed"


def test_reopen_task_rejects_already_pending() -> None:
    tasks = [Task("Study Python", "high", "", "pending")]

    with pytest.raises(ValueError, match="Task is already pending."):
        reopen_task(tasks, 1)


@pytest.mark.parametrize("task_number", [0, -1, 2])
def test_reopen_task_rejects_invalid_number(task_number: int) -> None:
    tasks = [Task("Study Python", "high", "", "completed")]

    with pytest.raises(InvalidNumberTasks):
        reopen_task(tasks, task_number)


def test_duplicate_ignores_status() -> None:
    existing_tasks = [
        Task("Study Python", "high", "", "completed"),
    ]

    new_task = Task("Study Python", "high", "", "pending")

    assert is_duplicate(new_task, existing_tasks) is True


def test_duplicate_rule_allows_different_priority_after_completion() -> None:
    existing_tasks = [
        Task("Study Python", "high", "", "completed"),
    ]

    new_task = Task("Study Python", "low", "", "pending")

    assert is_duplicate(new_task, existing_tasks) is False


def test_different_due_date_is_not_duplicate() -> None:
    existing_tasks = [
        Task("Study Python", "high", "2026-11-20", "completed"),
    ]

    new_task = Task("Study Python", "high", "2026-11-21", "pending")

    assert is_duplicate(new_task, existing_tasks) is False


def test_remove_duplicates_ignores_status() -> None:
    tasks = [
        Task("Study Python", "high", "", "completed"),
        Task("Study Python", "high", "", "pending"),
        Task("Buy groceries", "low", "", "pending"),
    ]

    result = remove_duplicate_tasks(tasks)

    assert result == [
        Task("Study Python", "high", "", "completed"),
        Task("Buy groceries", "low", "", "pending"),
    ]


def test_filter_tasks_by_status_preserves_original_tasks() -> None:
    tasks = [
        Task("Pending task", "low"),
        Task("Completed task", "high", "", "completed"),
    ]

    assert filter_tasks_by_status(tasks, "pending") == [tasks[0]]
    assert filter_tasks_by_status(tasks, "completed") == [tasks[1]]
    assert filter_tasks_by_status(tasks, "all") == tasks
    assert tasks[0].status == "pending"
    assert tasks[1].status == "completed"


def test_filter_tasks_by_status_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="Status must be one of"):
        filter_tasks_by_status([], "waiting")


@pytest.mark.parametrize(
    ("task", "today", "expected"),
    [
        (Task("Yesterday", "high", "2025-12-31"), date(2026, 1, 1), True),
        (Task("Today", "high", "2026-01-01"), date(2026, 1, 1), False),
        (Task("Tomorrow", "high", "2026-01-02"), date(2026, 1, 1), False),
        (Task("Completed", "high", "2025-12-31", "completed"), date(2026, 1, 1), False),
        (Task("No date", "high"), date(2026, 1, 1), False),
        (Task("Leap day", "high", "2024-02-29"), date(2024, 3, 1), True),
    ],
)
def test_is_overdue(task: Task, today: date, expected: bool) -> None:
    assert is_overdue(task, today) is expected


def test_filter_overdue_tasks_preserves_original_list() -> None:
    tasks = [
        Task("Past", "low", "2026-11-15"),
        Task("Today", "high", "2026-11-16"),
        Task("Completed past", "high", "2026-11-15", "completed"),
    ]

    assert filter_overdue_tasks(tasks, date(2026, 11, 16)) == [tasks[0]]
    assert len(tasks) == 3


def test_filter_tasks_by_priority_preserves_original_list() -> None:
    tasks = [Task("Low", "low"), Task("High", "high")]

    assert filter_tasks_by_priority(tasks, "high") == [tasks[1]]
    assert filter_tasks_by_priority(tasks, "low") == [tasks[0]]
    assert filter_tasks_by_priority(tasks, "all") == tasks
    assert len(tasks) == 2


def test_filter_tasks_by_priority_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="Priority filter must be one of"):
        filter_tasks_by_priority([], "urgent")
