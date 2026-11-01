from task_manager.models import InvalidNumberTasks, Task
from task_manager.tasks import create_task


def edit_task(
    tasks: list[Task],
    task_number: int,
    title: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
) -> tuple[Task, list[Task]]:
    """Edit a task and return it with the updated task list."""

    if task_number < 1 or task_number > len(tasks):
        raise InvalidNumberTasks("Task number does not exist.")

    original_task = tasks[task_number - 1]

    edited_task = create_task(
        title=original_task.title if title is None else title,
        priority=original_task.priority if priority is None else priority,
        due_date=original_task.due_date if due_date is None else due_date,
    )

    updated_tasks = list(tasks)
    updated_tasks[task_number - 1] = edited_task

    return edited_task, updated_tasks
