from task_manager.models import Task


def test_task_has_default_priority_and_no_due_date() -> None:
    task = Task("Study Finance")

    assert task.title == "Study Finance"
    assert task.priority == "medium"
    assert task.due_date == ""
