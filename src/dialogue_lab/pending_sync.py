"""Recovery records and allocation blocking after failed required writes."""

from collections.abc import Iterable, Mapping
from dataclasses import replace

from .errors import WriteSafetyError
from .identifiers import now_jerusalem
from .models import PendingSyncRecord


def create_pending_sync(
    *,
    operation: str,
    target_file: str,
    target_sheet: str,
    case_id: str,
    turn_id: str | None,
    expected_values: Mapping[str, object],
    failure: str,
    last_verified_state: Mapping[str, object],
    manual_version: str,
    source_revision_state: Mapping[str, str],
    required_reconciliation_action: str,
) -> PendingSyncRecord:
    required_text = {
        "operation": operation,
        "target_file": target_file,
        "target_sheet": target_sheet,
        "case_id": case_id,
        "failure": failure,
        "manual_version": manual_version,
        "required_reconciliation_action": required_reconciliation_action,
    }
    missing = [name for name, value in required_text.items() if not value.strip()]
    if missing:
        raise WriteSafetyError(f"incomplete PENDING SYNC record: {', '.join(missing)}")
    return PendingSyncRecord(
        operation=operation,
        target_file=target_file,
        target_sheet=target_sheet,
        case_id=case_id,
        turn_id=turn_id,
        expected_values=dict(expected_values),
        failure=failure,
        last_verified_state=dict(last_verified_state),
        manual_version=manual_version,
        source_revision_state=dict(source_revision_state),
        required_reconciliation_action=required_reconciliation_action,
        created_at=now_jerusalem().isoformat(timespec="seconds"),
    )


def unresolved_pending_sync(records: Iterable[PendingSyncRecord]) -> tuple[PendingSyncRecord, ...]:
    return tuple(record for record in records if not record.resolved)


def require_no_pending_sync(records: Iterable[PendingSyncRecord]) -> None:
    unresolved = unresolved_pending_sync(records)
    if unresolved:
        raise WriteSafetyError(
            f"operation blocked by {len(unresolved)} unresolved PENDING SYNC record(s)"
        )


def mark_reconciled(record: PendingSyncRecord) -> PendingSyncRecord:
    return replace(record, resolved=True)
