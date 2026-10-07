from task_manager.tasks import Task, add_task


def test_add_task() -> None:
    tasks: list[Task] = []

    task = add_task(tasks, "Study Finance", "high")

    assert task.title == "Study Finance"
    assert task.priority == "high"
    assert tasks == [task]