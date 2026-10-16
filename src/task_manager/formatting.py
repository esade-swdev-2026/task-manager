from task_manager.models import Task


def view_tasks(tasks: list[Task]) -> list[str]:
    lines: list[str] = []

    for index, task in enumerate(tasks, start=1):
        line = f"{index}. {task.title} - {task.priority}"

        if task.due_date != "":
            line = f"{line} - due {task.due_date}"

        lines.append(line)

    return lines
