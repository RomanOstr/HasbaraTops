"""Non-canonical, hash-only JSON Lines technical audit logging."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from .errors import DialogueLabError
from .models import TechnicalAuditEntry

AUDIT_FIELDS = frozenset(TechnicalAuditEntry.__dataclass_fields__)


def value_hash(values: Mapping[str, object]) -> str:
    canonical = json.dumps(
        values, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def append_audit_entry(path: Path, entry: TechnicalAuditEntry) -> None:
    """Append only the fixed metadata contract; never accept arbitrary public text fields."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(entry)
    if set(payload) != AUDIT_FIELDS:
        raise DialogueLabError("audit entry does not match the fixed metadata contract")
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def verify_audit_log(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as error:
                raise DialogueLabError(f"invalid audit JSON on line {line_number}") from error
            if not isinstance(payload, dict) or set(payload) != AUDIT_FIELDS:
                raise DialogueLabError(f"invalid audit fields on line {line_number}")
            for field in ("expected_value_hash", "read_back_hash", "schema_signature"):
                value = payload[field]
                if not isinstance(value, str) or len(value) != 64:
                    raise DialogueLabError(f"invalid {field} on line {line_number}")
            count += 1
    return count
