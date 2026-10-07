from task_manager.tasks import Task, add_task, view_tasks


def test_add_task() -> None:
    tasks: list[Task] = []

    task = add_task(tasks, "Study Finance", "high")

    assert task.title == "Study Finance"
    assert task.priority == "high"
    assert tasks == [task]

def test_view_tasks() -> None:
    tasks = [
        Task("Study Finance", "high"),
        Task("Buy groceries", "medium"),]

    result = view_tasks(tasks)

    assert result == [
        "1. Study Finance - high",
        "2. Buy groceries - medium", ]

def test_view_tasks_empty() -> None:
    tasks: list[Task] = []

    result = view_tasks(tasks)

    assert result == []