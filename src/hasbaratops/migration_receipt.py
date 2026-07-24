"""Deterministic migration receipt validation and rendering."""

import json
from collections.abc import Mapping

from .errors import HasbaraTopsError
from .models import MigrationReceipt, to_jsonable


def migration_receipt_from_mapping(payload: Mapping[str, object]) -> MigrationReceipt:
    required = set(MigrationReceipt.__dataclass_fields__)
    missing = sorted(required - payload.keys())
    extra = sorted(payload.keys() - required)
    if missing or extra:
        raise HasbaraTopsError(
            f"migration receipt fields mismatch; missing={missing}, extra={extra}"
        )
    case_id_map = payload["case_id_map"]
    if not isinstance(case_id_map, dict):
        raise HasbaraTopsError("migration receipt case_id_map must be a JSON object")
    backup_verified = payload["backup_verified"]
    if not isinstance(backup_verified, bool):
        raise HasbaraTopsError("migration receipt backup_verified must be a boolean")
    return MigrationReceipt(
        operation=str(payload["operation"]),
        cutover_timestamp=str(payload["cutover_timestamp"]),
        timezone=str(payload["timezone"]),
        database_schema_version_before=int(
            str(payload["database_schema_version_before"])
        ),
        database_schema_version_after=int(
            str(payload["database_schema_version_after"])
        ),
        database_integrity=str(payload["database_integrity"]),
        database_backup=str(payload["database_backup"]),
        migrated_case_count=int(str(payload["migrated_case_count"])),
        verified_turn_count=int(str(payload["verified_turn_count"])),
        first_case_id=str(payload["first_case_id"]),
        last_case_id=str(payload["last_case_id"]),
        case_id_map={str(key): str(value) for key, value in case_id_map.items()},
        backup_verified=backup_verified,
        committed_read_back=str(payload["committed_read_back"]),
        repository_commit=str(payload["repository_commit"]),
        test_results=str(payload["test_results"]),
        known_limitations=tuple(str(item) for item in _list(payload["known_limitations"])),
        rollback_instructions=tuple(str(item) for item in _list(payload["rollback_instructions"])),
    )


def _list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise HasbaraTopsError("migration receipt list field must be a JSON list")
    return value


def render_migration_receipt(receipt: MigrationReceipt) -> str:
    return json.dumps(to_jsonable(receipt), ensure_ascii=False, indent=2, sort_keys=True)
