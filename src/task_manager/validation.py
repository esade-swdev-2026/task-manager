import datetime

VALID_PRIORITIES = ("low", "medium", "high")


def normalize_title(title: str) -> str:
    normalized_title = title.strip()

    if normalized_title == "":
        raise ValueError("Title cannot be empty.")

    return normalized_title


def normalize_priority(priority: str) -> str:
    normalized_priority = priority.strip().lower()

    if normalized_priority not in VALID_PRIORITIES:
        allowed = ", ".join(VALID_PRIORITIES)
        raise ValueError(f"Priority must be one of: {allowed}.")

    return normalized_priority


def normalize_due_date(due_date: str) -> str:
    normalized_due_date = due_date.strip()

    if normalized_due_date == "":
        return ""

    try:
        parsed_date = datetime.date.fromisoformat(normalized_due_date)
    except ValueError:
        raise ValueError("Due date must use YYYY-MM-DD.") from None

    if parsed_date.isoformat() != normalized_due_date:
        raise ValueError("Due date must use YYYY-MM-DD.")

    return normalized_due_date
