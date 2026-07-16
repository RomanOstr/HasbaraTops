"""Live Case Log schema compatibility and deterministic signatures."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .enums import (
    CaseStatus,
    OutcomeClass,
    ParentConfidence,
    TurnDirection,
    TurnKind,
    TurnState,
)
from .errors import CompatibilityError
from .models import SchemaSignature

REQUIRED_SHEETS = (
    "Cases",
    "Turns",
    "Data Dictionary",
    "Strategy Taxonomy",
    "Dashboard",
)

CASE_HEADERS = (
    "Case ID", "Case Title", "Created At", "Updated At", "Status", "Topic",
    "Post Text", "Post URL", "Post ID", "Root Comment ID", "Source Links",
    "Privacy Checked", "Outcome Score 0–5", "Outcome Class", "Outcome Notes",
    "User Rating 1–5", "What Worked", "What Failed", "Next Test", "Closed At",
)

TURN_HEADERS = (
    "Case ID", "Turn ID", "Parent Turn ID", "Parent Confidence", "Participant Ref",
    "Direction", "Kind", "State", "Exact Text", "Post ID", "Root Comment ID",
    "Reply Comment ID", "Exact URL", "URL Supplied At", "Observed At", "Notes",
)

EXPECTED_ENUMS: dict[str, tuple[str, ...]] = {
    "Cases.Status": tuple(item.value for item in CaseStatus),
    "Cases.Privacy Checked": ("Yes", "No"),
    "Cases.Outcome Class": tuple(item.value for item in OutcomeClass),
    "Turns.Parent Confidence": tuple(item.value for item in ParentConfidence),
    "Turns.Direction": tuple(item.value for item in TurnDirection),
    "Turns.Kind": tuple(item.value for item in TurnKind),
    "Turns.State": tuple(item.value for item in TurnState),
}

ESSENTIAL_DASHBOARD_FORMULAS = (
    '=COUNTA(Cases!A2:A)',
    '=COUNTA(Turns!B2:B)',
    '=COUNTIF(Cases!E2:E,"Draft")',
    '=COUNTIF(Cases!E2:E,"Posted")',
    '=COUNTIF(Cases!E2:E,"Active Exchange")',
    '=COUNTIF(Cases!E2:E,"Closed*")',
)


def expected_schema_payload() -> dict[str, object]:
    return {
        "sheets": list(REQUIRED_SHEETS),
        "headers": {"Cases": list(CASE_HEADERS), "Turns": list(TURN_HEADERS)},
        "enums": {key: list(values) for key, values in EXPECTED_ENUMS.items()},
        "essential_dashboard_formulas": list(ESSENTIAL_DASHBOARD_FORMULAS),
    }


def schema_signature(payload: Mapping[str, object] | None = None) -> SchemaSignature:
    canonical = json.dumps(
        payload or expected_schema_payload(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return SchemaSignature(hashlib.sha256(canonical).hexdigest())


def _as_strings(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CompatibilityError(f"{label} must be a list")
    return tuple(str(item) for item in value)


def validate_schema(observed: Mapping[str, Any]) -> SchemaSignature:
    sheets = observed.get("sheets")
    if not isinstance(sheets, Mapping):
        raise CompatibilityError("schema JSON requires a sheets object")
    if set(sheets) != set(REQUIRED_SHEETS):
        raise CompatibilityError(
            f"sheet mismatch: expected {list(REQUIRED_SHEETS)}, observed {sorted(sheets)}"
        )
    expected_headers = {"Cases": CASE_HEADERS, "Turns": TURN_HEADERS}
    for sheet, expected in expected_headers.items():
        actual = _as_strings(sheets[sheet], f"{sheet} headers")
        if actual != expected:
            raise CompatibilityError(
                f"{sheet} header mismatch: expected {list(expected)}, observed {list(actual)}"
            )
    enums = observed.get("enums")
    if not isinstance(enums, Mapping):
        raise CompatibilityError("schema JSON requires an enums object")
    for field, expected in EXPECTED_ENUMS.items():
        if field not in enums:
            raise CompatibilityError(f"missing enum definition: {field}")
        actual = _as_strings(enums[field], field)
        if actual != expected:
            raise CompatibilityError(
                f"enum mismatch for {field}: expected {list(expected)}, observed {list(actual)}"
            )
    formulas = observed.get("dashboard_formulas")
    if formulas is not None:
        actual_formulas = set(_as_strings(formulas, "dashboard_formulas"))
        missing = [
            formula for formula in ESSENTIAL_DASHBOARD_FORMULAS if formula not in actual_formulas
        ]
        if missing:
            raise CompatibilityError(f"missing essential Dashboard formulas: {missing}")
    return schema_signature()
