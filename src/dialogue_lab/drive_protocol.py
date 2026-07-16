"""Provider-independent Drive protocol and write-policy boundary.

The Codex Google Drive plugin is runtime-managed and is not imported by Python.
Implementations must execute connector calls outside this package, then pass typed
responses back through deterministic validation and read-back comparison.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from .drive_models import ConnectorRequest
from .errors import WriteSafetyError
from .models import DriveWriteRequest, SourceRevisionState

CASE_LOG_ID = "1BysryBcXiA0W5xN_J_kdWj0wuf8RHweSkc6w1c3Tz8k"
GENERAL_RESPONSES_ID = "1Q10V7szfmcoDLme0y3KkDAn_WdYvXVGvwQS0yI-SiGU"
STRATEGY_GUIDE_ID = "1-IcaaAxzvPIDNYpO0gVpoI-bgWPOlKZz6-GhXsxJNpw"
EVIDENCE_BASE_ID = "1ULMsy7XncP_bXK2TPNJQHOPLcNg2t9eV9XeHMgoPxU0"


class DriveProtocol(Protocol):
    """Semantic operations required by Dialogue Lab workflows."""

    def read_operating_manual(self) -> tuple[str, SourceRevisionState]: ...
    def read_strategy_guide(self) -> tuple[str, SourceRevisionState]: ...
    def read_evidence_base(self) -> tuple[str, SourceRevisionState]: ...
    def read_case_log_schema(self) -> Mapping[str, object]: ...
    def read_case_rows(self) -> Sequence[Mapping[str, object]]: ...
    def read_turn_rows(self, case_id: str | None = None) -> Sequence[Mapping[str, object]]: ...
    def find_case_by_identity(
        self, post_id: str, root_comment_id: str
    ) -> Mapping[str, object] | None: ...
    def find_unresolved_pending_sync(self) -> Sequence[Mapping[str, object]]: ...
    def append_case(self, request: DriveWriteRequest) -> Mapping[str, object]: ...
    def update_case(self, request: DriveWriteRequest) -> Mapping[str, object]: ...
    def append_turn(self, request: DriveWriteRequest) -> Mapping[str, object]: ...
    def update_turn(self, request: DriveWriteRequest) -> Mapping[str, object]: ...
    def read_back_case(self, case_id: str) -> Mapping[str, object]: ...
    def read_back_turn(self, case_id: str, turn_id: str) -> Mapping[str, object]: ...
    def read_file_revision_state(self, file_id: str) -> SourceRevisionState: ...


def validate_drive_write_request(request: DriveWriteRequest) -> None:
    """Enforce the initial least-privilege, explicit-approval write policy."""
    if not request.explicitly_approved:
        raise WriteSafetyError("canonical writes require explicit user approval")
    if request.operation not in {"append_case", "update_case", "append_turn", "update_turn"}:
        raise WriteSafetyError(f"disabled Drive operation: {request.operation}")
    if request.target_file_id == GENERAL_RESPONSES_ID:
        if (
            not request.protected_override_instruction
            or not request.protected_override_instruction.strip()
        ):
            raise WriteSafetyError("General responses is protected and read-only")
        raise WriteSafetyError(
            "General responses cannot be written through the Case Log connector boundary"
        )
    if request.target_file_id in {STRATEGY_GUIDE_ID, EVIDENCE_BASE_ID}:
        raise WriteSafetyError("Strategy Guide and Evidence Base writes are never automatic")
    if request.target_file_id != CASE_LOG_ID:
        raise WriteSafetyError("write target is outside the configured Case Log")
    if request.target_sheet not in {"Cases", "Turns"}:
        raise WriteSafetyError("canonical Case Log writes are limited to Cases and Turns")
    if not request.record_identity.strip() or not request.values:
        raise WriteSafetyError("write request requires record identity and values")


def connector_request(
    request: DriveWriteRequest, source_revision_state: Mapping[str, str]
) -> ConnectorRequest:
    """Build a transport-neutral envelope after deterministic policy validation."""
    validate_drive_write_request(request)
    return ConnectorRequest(
        action=request.operation,
        file_id=request.target_file_id,
        sheet=request.target_sheet,
        payload={"record_identity": request.record_identity, "values": dict(request.values)},
        source_revision_state=dict(source_revision_state),
    )
