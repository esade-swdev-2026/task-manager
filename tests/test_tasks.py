import pytest

from task_manager.models import Task
from task_manager.tasks import (
    add_task,
    count_tasks_by_priority,
    create_task,
    delete_task,
    is_duplicate,
    remove_duplicate_tasks,
    sort_tasks_by_due_date,
    sort_tasks_by_priority,
)

GROCERIES = Task(
    "Buy groceries",
    "medium",
    "2026-11-17",
)
PRESENT = Task(
    "Buy Present",
    "low",
    "2027-12-02",
)
FINANCE = Task(
    "Study Finance",
    "high",
    "2026-12-01",
)
GYM = Task(
    "Go to the Gym",
    "low",
    "2026-11-04",
)
DOCTOR = Task(
    "Doctor Appointment",
    "high",
    "2026-10-31",
)
EARLY = Task(
    "Early task",
    "medium",
    "2026-10-01",
)
LATE = Task(
    "Late task",
    "medium",
    "2026-12-01",
)
NO_DATE = Task(
    "No date task",
    "medium",
)


def test_create_task_normalizes_values() -> None:
    result = create_task(
        "  Study Finance  ",
        "HIGH",
        "2026-12-01",
    )

    assert result == FINANCE


def test_create_task_rejects_empty_title() -> None:
    with pytest.raises(
        ValueError,
        match="Title cannot be empty",
    ):
        create_task("   ")


def test_create_task_rejects_invalid_priority() -> None:
    with pytest.raises(
        ValueError,
        match="Priority must be one of",
    ):
        create_task(
            "Study Finance",
            "urgent",
        )


def test_create_task_rejects_invalid_due_date() -> None:
    with pytest.raises(
        ValueError,
        match="Due date must use YYYY-MM-DD",
    ):
        create_task(
            "Study Finance",
            due_date="01-12-2026",
        )


def test_add_task() -> None:
    tasks: list[Task] = []

    task = add_task(
        tasks,
        "Study Finance",
        "high",
    )

    assert task == Task(
        "Study Finance",
        "high",
    )
    assert tasks == [task]


def test_count_empty_list_of_tasks() -> None:
    assert count_tasks_by_priority([]) == {
        "high": 0,
        "medium": 0,
        "low": 0,
    }


def test_count_different_priorities() -> None:
    tasks = [
        FINANCE,
        GROCERIES,
        GYM,
        PRESENT,
    ]

    assert count_tasks_by_priority(tasks) == {
        "high": 1,
        "medium": 1,
        "low": 2,
    }


def test_count_only_high_priority() -> None:
    result = count_tasks_by_priority([FINANCE, DOCTOR])

    assert result == {
        "high": 2,
        "medium": 0,
        "low": 0,
    }


def test_sort_by_priority() -> None:
    result = sort_tasks_by_priority(
        [
            GYM,
            GROCERIES,
            FINANCE,
        ]
    )

    assert result == [
        FINANCE,
        GROCERIES,
        GYM,
    ]


def test_sort_by_priority_empty() -> None:
    assert sort_tasks_by_priority([]) == []


def test_sort_by_priority_does_not_modify_original() -> None:
    tasks = [GYM, FINANCE]

    sort_tasks_by_priority(tasks)

    assert tasks == [GYM, FINANCE]


def test_sort_by_due_date_earliest_first() -> None:
    assert sort_tasks_by_due_date([LATE, EARLY]) == [
        EARLY,
        LATE,
    ]


def test_sort_by_due_date_puts_no_date_last() -> None:
    result = sort_tasks_by_due_date(
        [
            NO_DATE,
            LATE,
            EARLY,
        ]
    )

    assert result == [
        EARLY,
        LATE,
        NO_DATE,
    ]


def test_sort_by_due_date_empty() -> None:
    assert sort_tasks_by_due_date([]) == []


def test_sort_by_due_date_between_years() -> None:
    last_year_task = Task(
        "Old",
        "low",
        "2025-12-31",
    )
    this_year_task = Task(
        "New",
        "low",
        "2026-01-01",
    )

    result = sort_tasks_by_due_date(
        [
            this_year_task,
            last_year_task,
        ]
    )

    assert result == [
        last_year_task,
        this_year_task,
    ]


def test_sort_by_due_date_keeps_tie_order() -> None:
    first = Task(
        "First",
        "low",
        "2026-10-01",
    )
    second = Task(
        "Second",
        "high",
        "2026-10-01",
    )

    assert sort_tasks_by_due_date([first, second]) == [
        first,
        second,
    ]


def test_sort_by_due_date_does_not_modify_original() -> None:
    tasks = [LATE, EARLY]

    sort_tasks_by_due_date(tasks)

    assert tasks == [LATE, EARLY]


def test_remove_duplicates_empty() -> None:
    assert remove_duplicate_tasks([]) == []


def test_no_duplicates_remains_unchanged() -> None:
    tasks = [
        FINANCE,
        GYM,
        GROCERIES,
    ]

    assert remove_duplicate_tasks(tasks) == tasks


def test_remove_exact_duplicate() -> None:
    copy = Task(
        "Study Finance",
        "high",
        "2026-12-01",
    )

    assert remove_duplicate_tasks([FINANCE, copy]) == [FINANCE]


def test_remove_many_duplicates() -> None:
    assert remove_duplicate_tasks([GYM, GYM, GYM]) == [GYM]


def test_remove_duplicates_keeps_order() -> None:
    result = remove_duplicate_tasks(
        [
            GYM,
            FINANCE,
            GYM,
            GROCERIES,
            FINANCE,
        ]
    )

    assert result == [
        GYM,
        FINANCE,
        GROCERIES,
    ]


def test_same_name_different_priority_is_kept() -> None:
    low_task = Task("Eat Lunch", "low")
    high_task = Task("Eat Lunch", "high")

    assert remove_duplicate_tasks([low_task, high_task]) == [
        low_task,
        high_task,
    ]


def test_same_name_different_date_is_kept() -> None:
    first = Task(
        "Same title",
        "low",
        "2026-10-01",
    )
    second = Task(
        "Same title",
        "low",
        "2026-10-02",
    )

    assert remove_duplicate_tasks([first, second]) == [
        first,
        second,
    ]


def test_remove_duplicates_does_not_modify_original() -> None:
    tasks = [GYM, GYM]

    remove_duplicate_tasks(tasks)

    assert tasks == [GYM, GYM]


def test_exact_task_is_duplicate() -> None:
    assert (
        is_duplicate(
            FINANCE,
            [FINANCE],
        )
        is True
    )


def test_different_priority_is_not_duplicate() -> None:
    low_priority_task = Task(
        "Study Finance",
        "low",
        "2026-12-01",
    )

    assert (
        is_duplicate(
            FINANCE,
            [low_priority_task],
        )
        is False
    )


def test_different_date_is_not_duplicate() -> None:
    different_date = Task(
        "Study Finance",
        "high",
        "2026-12-02",
    )

    assert (
        is_duplicate(
            FINANCE,
            [different_date],
        )
        is False
    )


def test_delete_task_returns_deleted_and_remaining_tasks() -> None:
    tasks = [
        FINANCE,
        GROCERIES,
    ]

    deleted_task, remaining_tasks = delete_task(tasks, 1)

    assert deleted_task == FINANCE
    assert remaining_tasks == [GROCERIES]
    assert tasks == [
        FINANCE,
        GROCERIES,
    ]


def test_delete_task_rejects_zero() -> None:
    tasks = [
        FINANCE,
        GROCERIES,
    ]

    with pytest.raises(
        ValueError,
        match="Task number does not exist",
    ):
        delete_task(tasks, 0)


def test_delete_task_rejects_number_too_large() -> None:
    tasks = [
        FINANCE,
        GROCERIES,
    ]

    with pytest.raises(
        ValueError,
        match="Task number does not exist",
    ):
        delete_task(tasks, 3)
