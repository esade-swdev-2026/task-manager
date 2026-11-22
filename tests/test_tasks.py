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
    reopen_task,
    search_tasks,
    sort_tasks_by_due_date,
    sort_tasks_by_priority,
    task_summary,
    tasks_due_soon,
    tasks_due_today,
    tasks_for_today,
    weekly_review,
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


def test_delete_only_task_returns_empty_list() -> None:
    tasks = [FINANCE]

    deleted_task, remaining_tasks = delete_task(tasks, 1)

    assert deleted_task == FINANCE
    assert remaining_tasks == []
    assert tasks == [FINANCE]


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


def test_tasks_for_today_filters_and_sorts_by_due_date() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Due today", "high", "2026-11-17"),
        Task("Future", "low", "2026-11-18"),
        Task("Overdue yesterday", "medium", "2026-11-16"),
        Task("Completed overdue", "high", "2026-11-10", "completed"),
        Task("No due date", "low"),
        Task("Oldest overdue", "high", "2026-11-10"),
    ]

    result = tasks_for_today(tasks, today)

    assert result == [tasks[5], tasks[2], tasks[0]]


def test_tasks_for_today_returns_empty_when_no_tasks_match() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Future", "high", "2026-11-20"),
        Task("Completed today", "medium", "2026-11-17", "completed"),
        Task("No due date", "low"),
    ]

    assert tasks_for_today(tasks, today) == []
    assert tasks_for_today([], today) == []


def test_tasks_for_today_does_not_modify_original_list() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Due today", "high", "2026-11-17"),
        Task("Overdue", "low", "2026-11-15"),
    ]
    original_tasks = list(tasks)

    result = tasks_for_today(tasks, today)

    assert result == [tasks[1], tasks[0]]
    assert tasks == original_tasks
    assert result is not tasks


def test_tasks_due_soon_filters_and_sorts_by_date() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Day 7", "low", "2026-11-24"),
        Task("Overdue", "high", "2026-11-16"),
        Task("Day 1", "medium", "2026-11-18"),
        Task("Today", "high", "2026-11-17"),
        Task("Day 8", "high", "2026-11-25"),
        Task("Day 3", "high", "2026-11-20"),
        Task("Completed", "high", "2026-11-19", "completed"),
        Task("No date", "low"),
    ]

    result = tasks_due_soon(tasks, today)

    assert result == [tasks[2], tasks[5], tasks[0]]


def test_tasks_due_soon_returns_empty_when_no_tasks_match() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Today", "high", "2026-11-17"),
        Task("Too late", "medium", "2026-11-25"),
        Task("Completed", "low", "2026-11-18", "completed"),
        Task("No date", "medium"),
    ]

    assert tasks_due_soon(tasks, today) == []
    assert tasks_due_soon([], today) == []


def test_tasks_due_soon_does_not_modify_original_list() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Day 7", "low", "2026-11-24"),
        Task("Day 1", "high", "2026-11-18"),
    ]
    original_tasks = list(tasks)

    result = tasks_due_soon(tasks, today)

    assert result == [tasks[1], tasks[0]]
    assert result is not tasks
    assert tasks == original_tasks


def test_task_summary_calculates_correct_statistics() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Overdue high", "high", "2026-11-16"),
        Task("Today medium", "medium", "2026-11-17"),
        Task("Future low", "low", "2026-11-20"),
        Task("Completed high", "high", "2026-11-15", "completed"),
        Task("Completed medium", "medium", "", "completed"),
    ]

    result = task_summary(tasks, today)

    assert result == {
        "total": 5,
        "pending": 3,
        "completed": 2,
        "overdue": 1,
        "completion_rate": 40.0,
        "high": 2,
        "medium": 2,
        "low": 1,
    }


def test_task_summary_handles_empty_list() -> None:
    result = task_summary([], date(2026, 11, 17))

    assert result == {
        "total": 0,
        "pending": 0,
        "completed": 0,
        "overdue": 0,
        "completion_rate": 0.0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }


def test_task_summary_does_not_modify_original_tasks() -> None:
    tasks = [
        Task("Pending", "high", "2026-11-16"),
        Task("Completed", "low", "", "completed"),
    ]
    original_tasks = list(tasks)

    task_summary(tasks, date(2026, 11, 17))

    assert tasks == original_tasks
    assert tasks[0].status == "pending"
    assert tasks[1].status == "completed"


def test_weekly_review_returns_correct_tasks_and_completed_count() -> None:
    today = date(2026, 11, 17)

    tasks = [
        Task("Overdue", "high", "2026-11-16"),
        Task("Tomorrow", "medium", "2026-11-18"),
        Task("Day 7", "low", "2026-11-24"),
        Task("Day 8", "high", "2026-11-25"),
        Task("Due today", "medium", "2026-11-17"),
        Task("Completed", "high", "2026-11-15", "completed"),
        Task("No deadline", "low"),
    ]

    overdue, due_today, upcoming, completed = weekly_review(tasks, today)

    assert [task.title for task in overdue] == ["Overdue"]
    assert [task.title for task in due_today] == ["Due today"]
    assert [task.title for task in upcoming] == ["Tomorrow", "Day 7"]
    assert completed == 1


def test_weekly_review_handles_empty_tasks() -> None:
    overdue, due_today, upcoming, completed = weekly_review([], date(2026, 11, 17))

    assert overdue == []
    assert due_today == []
    assert upcoming == []
    assert completed == 0


def test_weekly_review_does_not_modify_original_tasks() -> None:
    tasks = [
        Task("Overdue", "high", "2026-11-16"),
        Task("Completed", "medium", "", "completed"),
    ]
    original_tasks = list(tasks)

    weekly_review(tasks, date(2026, 11, 17))

    assert tasks == original_tasks


def test_complete_daily_task_creates_next_occurrence() -> None:
    tasks = [Task("Study Python", "high", "2026-11-18", "pending", "daily")]

    completed, updated = complete_task(tasks, 1)

    assert completed.status == "completed"
    assert [task.due_date for task in updated] == ["2026-11-18", "2026-11-19"]
    assert updated[1].status == "pending"
    assert tasks[0].status == "pending"


@pytest.mark.parametrize(
    ("recurrence", "due_date", "expected_date"),
    [
        ("weekly", "2026-11-18", "2026-11-25"),
        ("monthly", "2026-01-31", "2026-03-02"),
        ("monthly", "2028-01-31", "2028-03-01"),
    ],
)
def test_complete_weekly_and_monthly_tasks(
    recurrence: str, due_date: str, expected_date: str
) -> None:
    tasks = [Task("Study Python", "high", due_date, "pending", recurrence)]

    _, updated = complete_task(tasks, 1)

    assert [task.due_date for task in updated] == [due_date, expected_date]


def test_create_recurring_task() -> None:
    task = create_task(
        "Study Python",
        "high",
        "2026-11-18",
        recurrence="weekly",
        repeat_until="2026-12-31",
    )

    assert task.recurrence == "weekly"
    assert task.repeat_until == "2026-12-31"


def test_create_recurring_task_requires_end_date() -> None:
    with pytest.raises(ValueError, match="Recurring tasks require an end date."):
        create_task(
            "Study Python",
            "high",
            "2026-11-18",
            recurrence="weekly",
        )


def test_create_recurring_task_requires_due_date() -> None:
    with pytest.raises(ValueError, match="Recurring tasks require a due date."):
        create_task("Study Python", recurrence="daily")


def test_create_task_rejects_invalid_recurrence() -> None:
    with pytest.raises(ValueError, match="Invalid recurrence."):
        create_task("Study Python", "high", "2026-11-18", recurrence="yearly")


def test_recompleting_recurring_task_does_not_duplicate_next() -> None:
    tasks = [Task("Study Python", "high", "2026-11-18", "pending", "daily")]

    _, after_first_completion = complete_task(tasks, 1)
    _, reopened = reopen_task(after_first_completion, 1)
    _, after_second_completion = complete_task(reopened, 1)

    assert len(after_second_completion) == 2
    assert after_second_completion[1].due_date == "2026-11-19"


def test_recurring_task_stops_after_last_inclusive_date() -> None:
    tasks = [Task("Study", "high", "2026-11-18", "pending", "daily", "2026-11-19")]

    _, first = complete_task(tasks, 1, date(2026, 11, 18))
    _, last = complete_task(first, 2, date(2026, 11, 19))

    assert [task.due_date for task in last] == ["2026-11-18", "2026-11-19"]
    assert all(task.status == "completed" for task in last)


def test_old_recurring_task_skips_missed_dates() -> None:
    task = Task("Study", "high", "2026-11-15", "pending", "daily", "2026-11-20")

    _, updated = complete_task([task], 1, date(2026, 11, 18))

    assert [item.due_date for item in updated] == ["2026-11-15", "2026-11-18"]


def test_monthly_recurrence_skips_missed_30_day_intervals() -> None:
    task = Task("Rent", "high", "2026-01-31", "pending", "monthly", "2026-04-30")

    _, updated = complete_task([task], 1, date(2026, 3, 1))

    assert updated[1].due_date == "2026-03-02"


def test_recurring_task_does_not_generate_date_after_end() -> None:
    task = Task("Study", "high", "2026-11-15", "pending", "daily", "2026-11-17")

    _, updated = complete_task([task], 1, date(2026, 11, 18))

    assert len(updated) == 1
    assert updated[0].status == "completed"


def test_create_recurring_task_rejects_end_before_first_date() -> None:
    with pytest.raises(ValueError, match="End date must be on or after the due date"):
        create_task("Study", due_date="2026-11-18", recurrence="daily", repeat_until="2026-11-17")


def test_create_task_with_category() -> None:
    task = create_task("Study Finance", category="university")

    assert task.category == "university"


def test_create_task_default_category() -> None:
    task = create_task("Study Finance")

    assert task.category == "other"


def test_weekly_review_includes_tasks_due_today() -> None:
    today = date(2026, 11, 19)

    tasks = [
        Task("Overdue task", "high", due_date="2026-11-18"),
        Task("Today's task", "medium", due_date="2026-11-19"),
        Task("Upcoming task", "low", due_date="2026-11-20"),
        Task(
            "Completed today",
            "high",
            due_date="2026-11-19",
            status="completed",
        ),
    ]

    overdue, due_today, upcoming, completed = weekly_review(tasks, today)

    assert [task.title for task in overdue] == ["Overdue task"]
    assert [task.title for task in due_today] == ["Today's task"]
    assert [task.title for task in upcoming] == ["Upcoming task"]
    assert completed == 1


def test_tasks_due_today_only_returns_pending_tasks_due_today() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Due today", "high", "2026-11-17"),
        Task("Future", "low", "2026-11-18"),
        Task("Overdue", "medium", "2026-11-16"),
        Task("Completed today", "high", "2026-11-17", "completed"),
        Task("No due date", "low"),
    ]
    result = tasks_due_today(tasks, today)

    assert result == [tasks[0]]


def test_complete_recurring_task_adopts_matching_pending_task() -> None:
    recurring_task = create_task(
        "Study Python",
        due_date="2026-11-27",
        recurrence="weekly",
        repeat_until="2026-12-18",
    )
    manual_task = create_task(
        "Study Python",
        due_date="2026-12-04",
        category="university",
    )

    completed_task, updated_tasks = complete_task(
        [recurring_task, manual_task], 1, date(2026, 11, 27)
    )

    assert completed_task.status == "completed"
    assert len(updated_tasks) == 2

    adopted_task = updated_tasks[1]
    assert adopted_task.status == "pending"
    assert adopted_task.due_date == "2026-12-04"
    assert adopted_task.category == "university"
    assert adopted_task.recurrence == "weekly"
    assert adopted_task.repeat_until == "2026-12-18"

    _, updated_tasks = complete_task(updated_tasks, 2, date(2026, 12, 4))

    assert len(updated_tasks) == 3
    assert updated_tasks[1].status == "completed"
    assert updated_tasks[2].due_date == "2026-12-11"
    assert updated_tasks[2].status == "pending"
    assert updated_tasks[2].repeat_until == "2026-12-18"


@pytest.mark.parametrize(
    "existing_task",
    [
        create_task("Study Python", due_date="2026-12-04", status="completed"),
        create_task(
            "Study Python",
            due_date="2026-12-04",
            recurrence="daily",
            repeat_until="2026-12-10",
        ),
    ],
    ids=["completed", "recurring"],
)
def test_complete_recurring_task_preserves_existing_match(existing_task: Task) -> None:
    recurring_task = create_task(
        "Study Python",
        due_date="2026-11-27",
        recurrence="weekly",
        repeat_until="2026-12-18",
    )

    completed_task, updated_tasks = complete_task(
        [recurring_task, existing_task], 1, date(2026, 11, 27)
    )

    assert completed_task.status == "completed"
    assert updated_tasks == [completed_task, existing_task]
