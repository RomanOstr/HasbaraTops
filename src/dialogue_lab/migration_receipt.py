"""Deterministic migration receipt validation and rendering."""

import json
from collections.abc import Mapping

from .errors import DialogueLabError
from .models import MigrationReceipt, to_jsonable


def migration_receipt_from_mapping(payload: Mapping[str, object]) -> MigrationReceipt:
    required = set(MigrationReceipt.__dataclass_fields__)
    missing = sorted(required - payload.keys())
    extra = sorted(payload.keys() - required)
    if missing or extra:
        raise DialogueLabError(
            f"migration receipt fields mismatch; missing={missing}, extra={extra}"
        )
    return MigrationReceipt(
        cutover_timestamp=str(payload["cutover_timestamp"]),
        timezone=str(payload["timezone"]),
        manual_version=str(payload["manual_version"]),
        manual_revision_state=str(payload["manual_revision_state"]),
        case_log_schema_signature=str(payload["case_log_schema_signature"]),
        case_log_modified_state=str(payload["case_log_modified_state"]),
        repository_commit=str(payload["repository_commit"]),
        repository_tag=str(payload["repository_tag"]),
        codex_environment=str(payload["codex_environment"]),
        drive_connection_status=str(payload["drive_connection_status"]),
        writer_enabled=bool(payload["writer_enabled"]),
        previous_writer_disabled=bool(payload["previous_writer_disabled"]),
        test_results=str(payload["test_results"]),
        known_limitations=tuple(str(item) for item in _list(payload["known_limitations"])),
        rollback_instructions=tuple(str(item) for item in _list(payload["rollback_instructions"])),
    )


def _list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise DialogueLabError("migration receipt list field must be a JSON list")
    return value


def render_migration_receipt(receipt: MigrationReceipt) -> str:
    return json.dumps(to_jsonable(receipt), ensure_ascii=False, indent=2, sort_keys=True)
