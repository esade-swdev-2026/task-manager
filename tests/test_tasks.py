from task_manager.tasks import Task, add_task, count_tasks_by_priority, view_tasks

GROCERIES = Task("Buy groceries", "medium")
PRESENT = Task("Buy Present", "low")
FINANCE = Task("Study Finance", "high")
GYM = Task("Go to the Gym", "low")
DOCTOR = Task("Doctor Appointment", "high")


def test_add_task() -> None:
    tasks: list[Task] = []

    task = add_task(tasks, "Study Finance", "high")

    assert task.title == "Study Finance"
    assert task.priority == "high"
    assert tasks == [task]


def test_view_tasks() -> None:
    tasks = [
        Task("Study Finance", "high"),
        Task("Buy groceries", "medium"),
    ]

    result = view_tasks(tasks)

    assert result == [
        "1. Study Finance - high",
        "2. Buy groceries - medium",
    ]


def test_view_tasks_empty() -> None:
    tasks: list[Task] = []

    result = view_tasks(tasks)

    assert result == []


def test_count_empty_list_of_tasks() -> None:
    tasks: list[Task] = []
    result = count_tasks_by_priority(tasks)
    assert result == {"high": 0, "medium": 0, "low": 0}


def test_count_tasks_with_different_priorities() -> None:
    tasks = [FINANCE, GROCERIES, GYM, PRESENT]
    result = count_tasks_by_priority(tasks)

    assert result == {"high": 1, "medium": 1, "low": 2}


def test_count_tasks_only_high_priotity() -> None:
    tasks = [FINANCE, DOCTOR]
    result = count_tasks_by_priority(tasks)

    assert result == {"high": 2, "medium": 0, "low": 0}
