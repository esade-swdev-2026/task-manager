import datetime

from task_manager.models import (
    EmptyTitleError,
    InvalidDueDate,
    InvalidPriority,
    InvalidStatus,
)

VALID_PRIORITIES = ("low", "medium", "high")
VALID_STATUSES = ("pending", "completed")


def normalize_title(title: str) -> str:
    normalized_title = title.strip()

    if normalized_title == "":
        raise EmptyTitleError("Title cannot be empty.")

    return normalized_title


def normalize_priority(priority: str) -> str:
    normalized_priority = priority.strip().lower()

    if normalized_priority not in VALID_PRIORITIES:
        allowed = ", ".join(VALID_PRIORITIES)
        raise InvalidPriority(f"Priority must be one of: {allowed}.")

    return normalized_priority


def normalize_due_date(due_date: str) -> str:
    normalized_due_date = due_date.strip()

    if normalized_due_date == "":
        return ""

    try:
        parsed_date = datetime.date.fromisoformat(normalized_due_date)
    except ValueError:
        raise InvalidDueDate("Due date must use YYYY-MM-DD.") from None

    if parsed_date.isoformat() != normalized_due_date:
        raise InvalidDueDate("Due date must use YYYY-MM-DD.")

    return normalized_due_date


def normalize_status(status: str) -> str:
    normalized_status = status.strip().lower()

    if normalized_status not in VALID_STATUSES:
        allowed = ", ".join(VALID_STATUSES)
        raise InvalidStatus(f"Status must be one of: {allowed}.")

    return normalized_status


def normalize_recurrence(recurrence: str) -> str:
    normalized = recurrence.strip().lower()

    if normalized not in ("none", "daily", "weekly", "monthly"):
        raise ValueError("Invalid recurrence.")

    return normalized
