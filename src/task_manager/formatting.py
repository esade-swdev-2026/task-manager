from datetime import date

from task_manager.models import Task
from task_manager.tasks import is_overdue


def view_tasks(
    tasks: list[Task],
    today: date,
    highlight_due_today: bool = False,
) -> list[str]:
    lines: list[str] = []

    for index, task in enumerate(tasks, start=1):
        status = f"[{task.status.upper()}]"

        if is_overdue(task, today):
            status = f"{status} [OVERDUE]"
        elif (
            highlight_due_today and task.status == "pending" and task.due_date == today.isoformat()
        ):
            status = f"{status} [DUE TODAY]"

        line = f"{index}. {status} {task.title} - {task.priority}"

        if task.due_date != "":
            line = f"{line} - due {task.due_date}"

        lines.append(line)

    return lines


def format_weekly_review(
    overdue_tasks: list[Task],
    upcoming_tasks: list[Task],
    completed_count: int,
    today: date,
) -> list[str]:
    lines = [
        "=" * 40,
        "              WEEKLY REVIEW",
        "=" * 40,
        today.strftime("%A, %d %B %Y"),
        "",
        f"OVERDUE TASKS ({len(overdue_tasks)})",
        "-" * 40,
    ]

    if overdue_tasks:
        for index, task in enumerate(overdue_tasks, start=1):
            lines.append(f"{index}. [OVERDUE] {task.title}")
            lines.append(f"   Priority: {task.priority.upper()} | Due: {task.due_date}")
    else:
        lines.append("No overdue tasks. Great job!")

    lines.extend(
        [
            "",
            f"UPCOMING - NEXT 7 DAYS ({len(upcoming_tasks)})",
            "-" * 40,
        ]
    )

    if upcoming_tasks:
        for index, task in enumerate(upcoming_tasks, start=1):
            lines.append(f"{index}. {task.title}")
            lines.append(f"   Priority: {task.priority.upper()} | Due: {task.due_date}")
    else:
        lines.append("No upcoming tasks.")

    lines.extend(
        [
            "",
            "-" * 40,
            f"CURRENTLY COMPLETED: {completed_count} TASKS",
            "=" * 40,
        ]
    )

    return lines
