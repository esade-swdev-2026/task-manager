from datetime import date

from task_manager.models import Task
from task_manager.tasks import is_overdue


def view_tasks(tasks: list[Task], today: date) -> list[str]:
    lines: list[str] = []

    for index, task in enumerate(tasks, start=1):
        status = f"[{task.status.upper()}]"

        if is_overdue(task, today):
            status = f"{status} [OVERDUE]"

        line = f"{index}. {status} {task.title} - {task.priority}"

        if task.due_date != "":
            line = f"{line} - due {task.due_date}"

        lines.append(line)

    return lines
