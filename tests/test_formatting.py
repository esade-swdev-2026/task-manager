from datetime import date

from task_manager.formatting import format_calendar, format_weekly_review, view_tasks
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


def test_calendar_displays_tasks_and_aligned_grid() -> None:
    tasks = [
        Task("Study Python", due_date="2026-11-23"),
        Task("Marketing assignment", due_date="2026-11-23"),
    ]

    lines = format_calendar(tasks, 2026, 11)
    output = "\n".join(lines)

    assert "NOVEMBER 2026" in output

    assert "23 [2]" in output

    assert "Study Python" in output
    assert "Marketing assignment" in output

    calendar_end = next(index for index, line in enumerate(lines) if line.startswith("└"))

    calendar_lines = [
        line for line in lines[: calendar_end + 1] if line.startswith(("┌", "├", "└", "│"))
    ]

    assert len({len(line) for line in calendar_lines}) == 1

    table_lines = [
        line for line in lines[calendar_end + 1 :] if line.startswith(("┌", "├", "└", "│"))
    ]

    assert len({len(line) for line in table_lines}) == 1


def test_calendar_without_tasks() -> None:
    lines = format_calendar([], 2026, 11)
    output = "\n".join(lines)

    assert "NOVEMBER 2026" in output
    assert "TASKS THIS MONTH (0)" in output
    assert "01" in output
    assert "30" in output


def test_calendar_only_shows_selected_month() -> None:
    tasks = [
        Task("November task", due_date="2026-11-23"),
        Task("December task", due_date="2026-12-05"),
        Task("No deadline"),
    ]

    output = "\n".join(format_calendar(tasks, 2026, 11))

    assert "November task" in output
    assert "December task" not in output
    assert "No deadline" not in output
    assert "TASKS THIS MONTH (1)" in output


def test_calendar_handles_leap_year() -> None:
    tasks = [Task("Leap day task", due_date="2028-02-29")]

    output = "\n".join(format_calendar(tasks, 2028, 2))

    assert "FEBRUARY 2028" in output
    assert "29 [1]" in output
    assert "Leap day task" in output


def test_format_weekly_review_includes_due_today() -> None:
    today = date(2026, 11, 19)

    due_today = [Task("Study Finance", "high")]

    lines = format_weekly_review(
        [],
        due_today,
        [],
        0,
        today,
    )

    assert "DUE TODAY (1)" in lines
    assert "1. [DUE TODAY] Study Finance" in lines
    assert "No tasks due today." not in lines


def test_format_weekly_review_with_no_due_today_tasks() -> None:
    today = date(2026, 11, 19)

    lines = format_weekly_review([], [], [], 0, today)

    assert "DUE TODAY (0)" in lines
    assert "No tasks due today." in lines


def test_format_weekly_review() -> None:
    today = date(2026, 11, 17)
    overdue_tasks = [
        Task("Submit assignment", "high", "2026-11-16"),
    ]
    due_today_tasks = [
        Task("Due today", "medium", "2026-11-17"),
    ]
    upcoming_tasks = [
        Task("Prepare presentation", "medium", "2026-11-20"),
        Task("Finish project", "low", "2026-11-24"),
    ]

    result = format_weekly_review(overdue_tasks, due_today_tasks, upcoming_tasks, 3, today)

    assert "OVERDUE TASKS (1)" in result
    assert "DUE TODAY (1)" in result
    assert "UPCOMING - NEXT 7 DAYS (2)" in result
    assert "CURRENTLY COMPLETED: 3 TASKS" in result


def test_format_weekly_review_without_overdue_tasks() -> None:
    result = format_weekly_review(
        [],
        [],
        [Task("Study Finance", "high", "2026-11-20")],
        2,
        date(2026, 11, 17),
    )

    assert "OVERDUE TASKS (0)" in result
    assert "No overdue tasks. Great job!" in result


def test_format_weekly_review_without_upcoming_tasks() -> None:
    result = format_weekly_review(
        [Task("Late assignment", "high", "2026-11-16")],
        [],
        [],
        0,
        date(2026, 11, 17),
    )

    assert "UPCOMING - NEXT 7 DAYS (0)" in result
    assert "No upcoming tasks." in result


def test_format_weekly_review_without_any_tasks() -> None:
    result = format_weekly_review(
        [],
        [],
        [],
        0,
        date(2026, 11, 17),
    )

    assert "OVERDUE TASKS (0)" in result
    assert "DUE TODAY (0)" in result
    assert "No tasks due today." in result
    assert "UPCOMING - NEXT 7 DAYS (0)" in result
    assert "No upcoming tasks." in result
