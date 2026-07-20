"""Case-local and date-local identifier allocation."""

import re
from collections.abc import Iterable
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .errors import IdentifierError

CASE_ID_RE = re.compile(r"^CASE-(\d{8})-(\d{3})$")
TURN_ID_RE = re.compile(r"^T(\d{3})$")
JERUSALEM = ZoneInfo("Asia/Jerusalem")


def now_jerusalem() -> datetime:
    return datetime.now(JERUSALEM)


def _require_unique(values: list[str], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise IdentifierError(f"duplicate {label}: {', '.join(duplicates)}")


def next_case_id(
    existing_ids: Iterable[str],
    *,
    on_date: date | None = None,
) -> str:
    """Allocate the next Jerusalem-date Case ID from freshly supplied rows."""
    values = list(existing_ids)
    _require_unique(values, "Case IDs")
    parsed: list[tuple[str, int]] = []
    for value in values:
        match = CASE_ID_RE.fullmatch(value)
        if match is None:
            raise IdentifierError(f"malformed Case ID: {value}")
        parsed.append((match.group(1), int(match.group(2))))
    target = (on_date or now_jerusalem().date()).strftime("%Y%m%d")
    sequence = max((number for day, number in parsed if day == target), default=0) + 1
    if sequence > 999:
        raise IdentifierError(f"Case ID sequence exhausted for {target}")
    return f"CASE-{target}-{sequence:03d}"


def next_turn_id(existing_ids: Iterable[str]) -> str:
    """Allocate the next Turn ID from rows already filtered to one case."""
    values = list(existing_ids)
    _require_unique(values, "Turn IDs")
    numbers: list[int] = []
    for value in values:
        match = TURN_ID_RE.fullmatch(value)
        if match is None:
            raise IdentifierError(f"malformed Turn ID: {value}")
        numbers.append(int(match.group(1)))
    sequence = max(numbers, default=0) + 1
    if sequence > 999:
        raise IdentifierError("Turn ID sequence exhausted for case")
    return f"T{sequence:03d}"
