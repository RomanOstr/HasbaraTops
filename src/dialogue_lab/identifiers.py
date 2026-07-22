"""Global Case and case-local Turn identifier allocation."""

import re
from collections.abc import Iterable
from datetime import datetime
from zoneinfo import ZoneInfo

from .errors import IdentifierError

CASE_ID_RE = re.compile(r"^Case-(\d{3,})$")
TURN_ID_RE = re.compile(r"^T(\d{3})$")
JERUSALEM = ZoneInfo("Asia/Jerusalem")


def now_jerusalem() -> datetime:
    return datetime.now(JERUSALEM)


def _require_unique(values: list[str], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise IdentifierError(f"duplicate {label}: {', '.join(duplicates)}")


def case_id_number(value: str) -> int:
    """Validate a canonical Case ID and return its positive sequence number."""
    match = CASE_ID_RE.fullmatch(value)
    if match is None:
        raise IdentifierError(f"malformed Case ID: {value}")
    number = int(match.group(1))
    if number < 1 or value != f"Case-{number:03d}":
        raise IdentifierError(f"malformed Case ID: {value}")
    return number


def next_case_id(
    existing_ids: Iterable[str],
) -> str:
    """Allocate the next globally sequential Case ID from freshly supplied rows."""
    values = list(existing_ids)
    _require_unique(values, "Case IDs")
    numbers: list[int] = []
    for value in values:
        numbers.append(case_id_number(value))
    sequence = max(numbers, default=0) + 1
    return f"Case-{sequence:03d}"


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
