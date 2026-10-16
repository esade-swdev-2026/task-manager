import pytest

from task_manager.validation import (
    normalize_due_date,
    normalize_priority,
    normalize_title,
)


def test_title_is_stripped() -> None:
    assert normalize_title("  Study Finance  ") == "Study Finance"


def test_empty_title_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Title cannot be empty",
    ):
        normalize_title("   ")


def test_priority_is_stripped_and_lowercase() -> None:
    assert normalize_priority(" HIGH ") == "high"


def test_invalid_priority_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Priority must be one of",
    ):
        normalize_priority("urgent")


def test_empty_due_date_is_allowed() -> None:
    assert normalize_due_date("") == ""


def test_valid_due_date_is_kept() -> None:
    assert normalize_due_date("2026-10-18") == "2026-10-18"


def test_invalid_due_date_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Due date must use YYYY-MM-DD",
    ):
        normalize_due_date("18-10-2026")
