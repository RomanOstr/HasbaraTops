"""Typed, provider-independent domain records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .enums import (
    CaseStatus,
    OutcomeClass,
    ParentConfidence,
    TurnDirection,
    TurnKind,
    TurnState,
)
from .errors import DialogueLabError


def _required(value: str, name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise DialogueLabError(f"{name} is required")
    return cleaned


@dataclass(frozen=True)
class CaseIdentity:
    post_id: str
    root_comment_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "post_id", _required(self.post_id, "post_id"))
        object.__setattr__(
            self, "root_comment_id", _required(self.root_comment_id, "root_comment_id")
        )

    @property
    def key(self) -> str:
        return f"facebook:{self.post_id}:{self.root_comment_id}"


@dataclass(frozen=True)
class ParsedFacebookURL:
    original_url: str
    normalized_host: str | None
    post_id: str | None
    root_comment_id: str | None
    reply_comment_id: str | None
    is_facebook_url: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, order=True)
class ManualVersion:
    major: int
    minor: int
    source_text: str = field(compare=False, default="")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


@dataclass(frozen=True)
class SchemaSignature:
    value: str


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    case_title: str
    created_at: str
    updated_at: str
    status: CaseStatus
    topic: str
    post_text: str
    post_url: str
    post_id: str
    root_comment_id: str
    source_links: tuple[str, ...] = ()
    privacy_checked: bool = False
    outcome_score: int | None = None
    outcome_class: OutcomeClass | None = None
    outcome_notes: str = ""
    user_rating: int | None = None
    what_worked: str = ""
    what_failed: str = ""
    next_test: str = ""
    closed_at: str = ""

    @property
    def identity(self) -> CaseIdentity:
        return CaseIdentity(self.post_id, self.root_comment_id)


@dataclass(frozen=True)
class TurnRecord:
    case_id: str
    turn_id: str
    parent_turn_id: str | None
    parent_confidence: ParentConfidence | None
    participant_ref: str
    direction: TurnDirection
    kind: TurnKind
    state: TurnState
    exact_text: str
    post_id: str
    root_comment_id: str
    reply_comment_id: str | None = None
    exact_url: str | None = None
    url_supplied_at: str | None = None
    observed_at: str = ""
    notes: str = ""


@dataclass(frozen=True)
class LifecycleTransition:
    from_status: CaseStatus
    to_status: CaseStatus
    reason: str


@dataclass(frozen=True)
class PendingSyncRecord:
    operation: str
    target_file: str
    target_sheet: str
    case_id: str
    turn_id: str | None
    expected_values: Mapping[str, object]
    failure: str
    last_verified_state: Mapping[str, object]
    manual_version: str
    source_revision_state: Mapping[str, str]
    required_reconciliation_action: str
    created_at: str
    resolved: bool = False


@dataclass(frozen=True)
class DriveWriteRequest:
    operation: str
    target_file_id: str
    target_sheet: str
    record_identity: str
    values: Mapping[str, object]
    explicitly_approved: bool
    protected_override_instruction: str | None = None


@dataclass(frozen=True)
class DriveWriteVerification:
    succeeded: bool
    expected: Mapping[str, object]
    actual: Mapping[str, object]
    mismatches: tuple[str, ...]


@dataclass(frozen=True)
class ThreadMapEntry:
    turn_id: str
    parent_turn_id: str | None
    participant_ref: str
    excerpt: str
    state: TurnState


@dataclass(frozen=True)
class SourceRevisionState:
    source: str
    file_id: str
    revision_or_modified_time: str


@dataclass(frozen=True)
class SourceConsistencyResult:
    consistent: bool
    operation_start: Mapping[str, str]
    current: Mapping[str, str]
    changed_sources: tuple[str, ...]
    requires_reload: bool
    blocking_reasons: tuple[str, ...]


@dataclass(frozen=True)
class TechnicalAuditEntry:
    timestamp: str
    operation: str
    canonical_file_id: str
    sheet: str
    record_locator: str
    case_id: str
    turn_id: str | None
    expected_value_hash: str
    read_back_hash: str
    verification_result: bool
    manual_version: str
    manual_revision_state: str
    schema_signature: str
    git_commit: str
    error_category: str | None = None


@dataclass(frozen=True)
class MigrationReceipt:
    cutover_timestamp: str
    timezone: str
    manual_version: str
    manual_revision_state: str
    case_log_schema_signature: str
    case_log_modified_state: str
    repository_commit: str
    repository_tag: str
    codex_environment: str
    drive_connection_status: str
    writer_enabled: bool
    previous_writer_disabled: bool
    test_results: str
    known_limitations: tuple[str, ...]
    rollback_instructions: tuple[str, ...]


def to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses and enums to JSON-compatible values."""
    if hasattr(value, "__dataclass_fields__"):
        return to_jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_jsonable(item) for item in value]
    return value
