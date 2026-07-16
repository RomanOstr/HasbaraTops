"""Synthetic records shared by deterministic tests."""

from dialogue_lab.enums import (
    CaseStatus,
    ParentConfidence,
    TurnDirection,
    TurnKind,
    TurnState,
)
from dialogue_lab.models import CaseRecord, TurnRecord


def make_case(**overrides: object) -> CaseRecord:
    values: dict[str, object] = {
        "case_id": "CASE-20260717-001",
        "case_title": "Synthetic policy discussion",
        "created_at": "2026-07-17 10:00",
        "updated_at": "2026-07-17 10:00",
        "status": CaseStatus.POSTED,
        "topic": "Synthetic topic",
        "post_text": "Synthetic public post text.",
        "post_url": "https://www.facebook.com/example/posts/123",
        "post_id": "123",
        "root_comment_id": "456",
        "privacy_checked": True,
    }
    values.update(overrides)
    return CaseRecord(**values)  # type: ignore[arg-type]


def make_turn(**overrides: object) -> TurnRecord:
    values: dict[str, object] = {
        "case_id": "CASE-20260717-001",
        "turn_id": "T001",
        "parent_turn_id": None,
        "parent_confidence": None,
        "participant_ref": "P1",
        "direction": TurnDirection.INCOMING,
        "kind": TurnKind.COMMENT,
        "state": TurnState.RECEIVED,
        "exact_text": "Synthetic public comment.",
        "post_id": "123",
        "root_comment_id": "456",
        "observed_at": "2026-07-17 10:00",
    }
    values.update(overrides)
    return TurnRecord(**values)  # type: ignore[arg-type]


def make_reply(turn_id: str, parent: str, **overrides: object) -> TurnRecord:
    values: dict[str, object] = {
        "turn_id": turn_id,
        "parent_turn_id": parent,
        "parent_confidence": ParentConfidence.USER_CONFIRMED,
        "kind": TurnKind.REPLY,
    }
    values.update(overrides)
    return make_turn(**values)
