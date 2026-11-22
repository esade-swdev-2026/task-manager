from task_manager.models import Task
from task_manager.tasks import create_task, get_task


def edit_task(
    tasks: list[Task],
    task_number: int,
    title: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
    category: str | None = None,
) -> tuple[Task, list[Task]]:
    """Edit a task and return it with the updated task list."""

    original_task = get_task(tasks, task_number)

    edited_task = create_task(
        title=original_task.title if title is None else title,
        priority=original_task.priority if priority is None else priority,
        due_date=original_task.due_date if due_date is None else due_date,
        status=original_task.status,
        recurrence=original_task.recurrence,
        repeat_until=original_task.repeat_until,
        category=original_task.category if category is None else category,
    )

    updated_tasks = list(tasks)
    updated_tasks[task_number - 1] = edited_task

    return edited_task, updated_tasks
