from task_manager.tasks import (
    Task,
    add_task,
    count_tasks_by_priority,
    remove_duplicate_tasks,
    sort_tasks_by_due_date,
    sort_tasks_by_priority,
    view_tasks,
)

GROCERIES = Task("Buy groceries", "medium", "2026-11-17")
PRESENT = Task("Buy Present", "low", "2027-12-02")
FINANCE = Task("Study Finance", "high", "2026-12-01")
GYM = Task("Go to the Gym", "low", "2026-11-04")
DOCTOR = Task("Doctor Appointment", "high", "2026-10-31")
EARLY = Task("Early task", "medium", "2026-10-01")
LATE = Task("Late task", "medium", "2026-12-01")
NO_DATE = Task("No date task", "medium")


# Tests for add_task


def test_add_task() -> None:
    tasks: list[Task] = []

    task = add_task(tasks, "Study Finance", "high")

    assert task.title == "Study Finance"
    assert task.priority == "high"
    assert tasks == [task]


# Tests for view_tasks


def test_view_tasks() -> None:
    tasks = [
        Task("Study Finance", "high"),
        Task("Buy groceries", "medium"),
    ]

    result = view_tasks(tasks)

    assert result == [
        "1. Study Finance - high",
        "2. Buy groceries - medium",
    ]


def test_view_tasks_empty() -> None:
    tasks: list[Task] = []

    result = view_tasks(tasks)

    assert result == []


# Tests for count_tasks_by_priority


def test_count_empty_list_of_tasks() -> None:
    tasks: list[Task] = []
    result = count_tasks_by_priority(tasks)
    assert result == {"high": 0, "medium": 0, "low": 0}


def test_count_tasks_with_different_priorities() -> None:
    tasks = [FINANCE, GROCERIES, GYM, PRESENT]
    result = count_tasks_by_priority(tasks)

    assert result == {"high": 1, "medium": 1, "low": 2}


def test_count_tasks_only_high_priotity() -> None:
    tasks = [FINANCE, DOCTOR]
    result = count_tasks_by_priority(tasks)

    assert result == {"high": 2, "medium": 0, "low": 0}


def test_sort_by_priority_orders_high_medium_low() -> None:
    result = sort_tasks_by_priority([GYM, GROCERIES, FINANCE])
    assert result == [FINANCE, GROCERIES, GYM]


def test_sort_by_priority_empty() -> None:
    assert sort_tasks_by_priority([]) == []


def test_sort_by_priority_does_not_modify_original() -> None:
    tasks = [GYM, FINANCE]
    sort_tasks_by_priority(tasks)
    assert tasks == [GYM, FINANCE]


# Tests for sort_tasks_by_due_date


def test_sort_by_due_date_earliest_first() -> None:
    assert sort_tasks_by_due_date([LATE, EARLY]) == [EARLY, LATE]


def test_sort_by_due_date_puts_no_date_last() -> None:
    result = sort_tasks_by_due_date([NO_DATE, LATE, EARLY])
    assert result == [EARLY, LATE, NO_DATE]


def test_sort_by_due_date_empty() -> None:
    assert sort_tasks_by_due_date([]) == []


def test_sort_by_due_date_compare_between_years() -> None:
    last_year_task = Task("Old", "low", "2025-12-31")
    this_year_task = Task("New", "low", "2026-01-01")
    assert sort_tasks_by_due_date([this_year_task, last_year_task]) == [
        last_year_task,
        this_year_task,
    ]  # noqa: E501


def test_sort_by_due_date_list_order_stays_same_for_ties() -> None:
    first = Task("First", "low", "2026-10-01")
    second = Task("Second", "high", "2026-10-01")
    assert sort_tasks_by_due_date([first, second]) == [first, second]


def test_sort_by_due_date_does_not_modify_original() -> None:
    tasks = [LATE, EARLY]
    sort_tasks_by_due_date(tasks)
    assert tasks == [LATE, EARLY]


# Tests for remove_duplicate_tasks


def test_remove_duplicates_empty() -> None:
    assert remove_duplicate_tasks([]) == []


def test_remove_duplicates_no_duplicates_unchanged() -> None:
    tasks = [FINANCE, GYM, GROCERIES]
    assert remove_duplicate_tasks(tasks) == tasks


def test_remove_duplicates_removes_exact_copy() -> None:
    copy = Task("Study Finance", "high", "2026-12-01")
    assert remove_duplicate_tasks([FINANCE, copy]) == [FINANCE]


def test_remove_duplicates_removes_many_copies() -> None:
    assert remove_duplicate_tasks([GYM, GYM, GYM]) == [GYM]


def test_remove_duplicates_keeps_first_occurrence_order() -> None:
    result = remove_duplicate_tasks([GYM, FINANCE, GYM, GROCERIES, FINANCE])
    assert result == [GYM, FINANCE, GROCERIES]


def test_remove_duplicates_same_name_different_priority() -> None:
    low_priority_task = Task("Eat Lunch", "low")
    high_priority_task = Task("Eat Lunch", "high")
    assert remove_duplicate_tasks([low_priority_task, high_priority_task]) == [
        low_priority_task,
        high_priority_task,
    ]  # noqa: E501


def test_remove_duplicates_same_name_different_due_date() -> None:
    task_a = Task("Same title", "low", "2026-10-01")
    task_b = Task("Same title", "low", "2026-10-02")
    assert remove_duplicate_tasks([task_a, task_b]) == [task_a, task_b]


def test_remove_duplicates_input_list_not_modified_stays_same() -> None:
    tasks = [GYM, GYM]
    remove_duplicate_tasks(tasks)
    assert tasks == [GYM, GYM]
