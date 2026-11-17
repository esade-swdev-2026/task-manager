from datetime import date

from task_manager.formatting import format_weekly_review, view_tasks
from task_manager.models import Task


def test_view_tasks() -> None:
    tasks = [Task("Study Finance", "high"), Task("Buy groceries", "medium")]

    assert view_tasks(tasks, date(2026, 11, 16)) == [
        "1. [PENDING] Study Finance - high",
        "2. [PENDING] Buy groceries - medium",
    ]


def test_view_task_with_due_date() -> None:
    tasks = [Task("Submit assignment", "high", "2026-10-18")]

    assert view_tasks(tasks, date(2026, 10, 18)) == [
        "1. [PENDING] Submit assignment - high - due 2026-10-18"
    ]


def test_view_tasks_empty() -> None:
    assert view_tasks([], date(2026, 11, 16)) == []


def test_view_tasks_displays_status() -> None:
    tasks = [
        Task("Study Python", "high", "", "pending"),
        Task("Buy groceries", "medium", "2026-11-20", "completed"),
    ]

    assert view_tasks(tasks, date(2026, 11, 19)) == [
        "1. [PENDING] Study Python - high",
        "2. [COMPLETED] Buy groceries - medium - due 2026-11-20",
    ]


def test_view_tasks_marks_only_overdue_pending_tasks() -> None:
    tasks = [
        Task("Late", "high", "2026-11-15"),
        Task("Due today", "medium", "2026-11-16"),
        Task("Completed late", "low", "2026-11-14", "completed"),
        Task("No due date", "low"),
    ]

    assert view_tasks(tasks, date(2026, 11, 16)) == [
        "1. [PENDING] [OVERDUE] Late - high - due 2026-11-15",
        "2. [PENDING] Due today - medium - due 2026-11-16",
        "3. [COMPLETED] Completed late - low - due 2026-11-14",
        "4. [PENDING] No due date - low",
    ]


def test_view_tasks_highlights_due_today_when_enabled() -> None:
    today = date(2026, 11, 17)
    tasks = [
        Task("Overdue task", "high", "2026-11-16"),
        Task("Due today", "medium", "2026-11-17"),
        Task("Completed today", "low", "2026-11-17", "completed"),
    ]

    result = view_tasks(tasks, today, highlight_due_today=True)

    assert "[OVERDUE] Overdue task" in result[0]
    assert "[DUE TODAY] Due today" in result[1]
    assert "[DUE TODAY]" not in result[2]


def test_view_tasks_preserves_default_format_for_due_today() -> None:
    today = date(2026, 11, 17)
    tasks = [Task("Due today", "high", "2026-11-17")]

    result = view_tasks(tasks, today)

    assert result == ["1. [PENDING] Due today - high - due 2026-11-17"]


def test_format_weekly_review() -> None:
    today = date(2026, 11, 17)
    overdue_tasks = [
        Task("Submit assignment", "high", "2026-11-16"),
    ]
    upcoming_tasks = [
        Task("Prepare presentation", "medium", "2026-11-20"),
        Task("Finish project", "low", "2026-11-24"),
    ]

    result = format_weekly_review(overdue_tasks, upcoming_tasks, 3, today)

    assert result == [
        "=" * 40,
        "              WEEKLY REVIEW",
        "=" * 40,
        "Tuesday, 17 November 2026",
        "",
        "OVERDUE TASKS (1)",
        "-" * 40,
        "1. [OVERDUE] Submit assignment",
        "   Priority: HIGH | Due: 2026-11-16",
        "",
        "UPCOMING - NEXT 7 DAYS (2)",
        "-" * 40,
        "1. Prepare presentation",
        "   Priority: MEDIUM | Due: 2026-11-20",
        "2. Finish project",
        "   Priority: LOW | Due: 2026-11-24",
        "",
        "-" * 40,
        "CURRENTLY COMPLETED: 3 TASKS",
        "=" * 40,
    ]


def test_format_weekly_review_without_overdue_tasks() -> None:
    result = format_weekly_review(
        [],
        [Task("Study Finance", "high", "2026-11-20")],
        2,
        date(2026, 11, 17),
    )

    assert "OVERDUE TASKS (0)" in result
    assert "No overdue tasks. Great job!" in result
    assert any("Study Finance" in line for line in result)


def test_format_weekly_review_without_upcoming_tasks() -> None:
    result = format_weekly_review(
        [Task("Late assignment", "high", "2026-11-16")],
        [],
        0,
        date(2026, 11, 17),
    )

    assert "UPCOMING - NEXT 7 DAYS (0)" in result
    assert "No upcoming tasks." in result
    assert any("Late assignment" in line for line in result)


def test_format_weekly_review_without_any_tasks() -> None:
    result = format_weekly_review(
        [],
        [],
        0,
        date(2026, 11, 17),
    )

    assert "OVERDUE TASKS (0)" in result
    assert "UPCOMING - NEXT 7 DAYS (0)" in result
    assert "CURRENTLY COMPLETED: 0 TASKS" in result
    assert "No overdue tasks. Great job!" in result
    assert "No upcoming tasks." in result
