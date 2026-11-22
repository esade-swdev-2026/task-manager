from task_manager.models import Task


def test_task_has_default_values() -> None:
    task = Task("Study Finance")

    assert task.title == "Study Finance"
    assert task.priority == "medium"
    assert task.due_date == ""
    assert task.status == "pending"
    assert task.recurrence == "none"
    assert task.repeat_until == ""
    assert task.category == "other"


def test_task_has_custom_category() -> None:
    task = Task("Study Finance", category="university")

    assert task.category == "university"
