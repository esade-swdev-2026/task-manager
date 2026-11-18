from calendar import month_name, monthcalendar
from collections import Counter
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


def format_calendar(tasks: list[Task], year: int, month: int) -> list[str]:
    """Format a monthly calendar and its task details as aligned tables."""

    weeks = monthcalendar(year, month)
    month_prefix = f"{year:04d}-{month:02d}-"

    month_tasks = sorted(
        [task for task in tasks if task.due_date.startswith(month_prefix)],
        key=lambda task: (task.due_date, task.title.lower()),
    )

    task_counts = Counter(int(task.due_date[-2:]) for task in month_tasks)

    cell_width = max([8] + [len(f"{day:02d} [{count}]") for day, count in task_counts.items()])

    horizontal = "─" * cell_width

    top = "┌" + "┬".join([horizontal] * 7) + "┐"
    middle = "├" + "┼".join([horizontal] * 7) + "┤"
    bottom = "└" + "┴".join([horizontal] * 7) + "┘"

    lines = [
        f"CALENDAR VIEW — {month_name[month].upper()} {year}",
        top,
        "│"
        + "│".join(
            f"{day:^{cell_width}}" for day in ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
        )
        + "│",
        middle,
    ]

    for index, week in enumerate(weeks):
        cells = []

        for day in week:
            if day == 0:
                label = ""
            elif task_counts[day]:
                label = f"{day:02d} [{task_counts[day]}]"
            else:
                label = f"{day:02d}"

            cells.append(f"{label:^{cell_width}}")

        lines.append("│" + "│".join(cells) + "│")

        if index < len(weeks) - 1:
            lines.append(middle)

    lines.append(bottom)

    lines.append("")
    lines.append(f"TASKS THIS MONTH ({len(month_tasks)})")

    headers = ("DATE", "TASK", "STATUS", "PRIORITY")
    rows = [
        (
            task.due_date[-2:],
            task.title,
            task.status.capitalize(),
            task.priority.capitalize(),
        )
        for task in month_tasks
    ]

    widths = [
        max([len(header)] + [len(row[index]) for row in rows])
        for index, header in enumerate(headers)
    ]

    def table_border(left: str, middle_char: str, right: str) -> str:
        return left + middle_char.join("─" * (width + 2) for width in widths) + right

    def table_row(values: tuple[str, str, str, str]) -> str:
        return (
            "│"
            + "│".join(f" {value:<{width}} " for value, width in zip(values, widths, strict=True))
            + "│"
        )

    lines.append(table_border("┌", "┬", "┐"))
    lines.append(table_row(headers))
    lines.append(table_border("├", "┼", "┤"))

    for row in rows:
        lines.append(table_row(row))

    lines.append(table_border("└", "┴", "┘"))

    return lines
