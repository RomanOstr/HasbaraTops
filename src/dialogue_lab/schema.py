"""Canonical SQLite schema metadata and deterministic signatures."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from .enums import (
    CaseStatus,
    OutcomeClass,
    ParentConfidence,
    TurnDirection,
    TurnKind,
    TurnState,
)
from .models import SchemaSignature

SCHEMA_VERSION = 1

CASE_FIELDS = (
    "case_id",
    "case_title",
    "created_at",
    "updated_at",
    "status",
    "topic",
    "post_text",
    "post_url",
    "post_id",
    "root_comment_id",
    "source_links",
    "privacy_checked",
    "outcome_score",
    "outcome_class",
    "outcome_notes",
    "user_rating",
    "what_worked",
    "what_failed",
    "next_test",
    "closed_at",
)

TURN_FIELDS = (
    "case_id",
    "turn_id",
    "parent_turn_id",
    "parent_confidence",
    "participant_ref",
    "direction",
    "kind",
    "state",
    "exact_text",
    "post_id",
    "root_comment_id",
    "reply_comment_id",
    "exact_url",
    "url_supplied_at",
    "observed_at",
    "notes",
)

EXPECTED_ENUMS: dict[str, tuple[str, ...]] = {
    "cases.status": tuple(item.value for item in CaseStatus),
    "cases.outcome_class": tuple(item.value for item in OutcomeClass),
    "turns.parent_confidence": tuple(item.value for item in ParentConfidence),
    "turns.direction": tuple(item.value for item in TurnDirection),
    "turns.kind": tuple(item.value for item in TurnKind),
    "turns.state": tuple(item.value for item in TurnState),
}


def expected_schema_payload() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tables": {"cases": list(CASE_FIELDS), "turns": list(TURN_FIELDS)},
        "enums": {key: list(values) for key, values in EXPECTED_ENUMS.items()},
        "constraints": [
            "cases.case_id primary key",
            "cases.case_id canonical positive Case-NNN check",
            "cases(post_id, root_comment_id) candidate index",
            "turns(case_id, turn_id) primary key",
            "turns.case_id references cases.case_id",
            "turns.reply_comment_id globally unique when present",
            "turns(case_id, coalesced parent_turn_id, direction, exact_text) unique "
            "when reply_comment_id absent",
        ],
    }


def schema_signature(payload: Mapping[str, object] | None = None) -> SchemaSignature:
    canonical = json.dumps(
        payload or expected_schema_payload(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return SchemaSignature(hashlib.sha256(canonical).hexdigest())
