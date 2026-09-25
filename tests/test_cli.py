from typer.testing import CliRunner

from task_manager.cli import app, tasks

runner = CliRunner()

def test_add_task_default_priority() -> None:
    tasks.clear()

    result = runner.invoke(app, ["add", "Study Finance"])

    assert result.exit_code == 0
    assert tasks[0]["title"] == "Study Finance"
    assert tasks[0]["priority"] == "medium"


def test_add_task_high_priority() -> None:
    tasks.clear()

    result = runner.invoke(app, ["add", "Study Finance", "--priority", "high"])

    assert result.exit_code == 0
    assert tasks[0]["title"] == "Study Finance"
    assert tasks[0]["priority"] == "high"

