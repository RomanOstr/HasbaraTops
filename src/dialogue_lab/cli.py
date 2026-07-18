"""Installable command-line interface for deterministic Dialogue Lab operations."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

from . import __version__
from .case_identity import make_case_identity
from .enums import CaseStatus, OutcomeClass, ParentConfidence, TurnDirection, TurnKind, TurnState
from .errors import DialogueLabError
from .facebook_url import parse_facebook_url
from .identifiers import next_case_id, next_turn_id
from .lifecycle import validate_transition
from .manual_version import require_supported_manual
from .migration_receipt import migration_receipt_from_mapping, render_migration_receipt
from .models import (
    CaseRecord,
    LifecycleTransition,
    PendingSyncRecord,
    TurnRecord,
    to_jsonable,
)
from .parent_graph import validate_parent_graph
from .pending_sync import require_no_pending_sync
from .readback import verify_readback
from .schema import schema_signature, validate_schema
from .source_consistency import check_source_consistency
from .validation import validate_case, validate_turn


def _load_json(path: str) -> object:
    with Path(path).open(encoding="utf-8") as stream:
        value: object = json.load(stream)
    return value


def _mapping(value: object, label: str = "JSON document") -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise DialogueLabError(f"{label} must be a JSON object")
    return value


def _list(value: object, label: str = "JSON document") -> list[object]:
    if not isinstance(value, list):
        raise DialogueLabError(f"{label} must be a JSON list")
    return value


def _optional_string(value: object) -> str | None:
    return None if value is None else str(value)


def _case_record(payload: Mapping[str, Any]) -> CaseRecord:
    links = payload.get("source_links", [])
    return CaseRecord(
        case_id=str(payload.get("case_id", "")),
        case_title=str(payload.get("case_title", "")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        status=CaseStatus(str(payload.get("status", ""))),
        topic=str(payload.get("topic", "")),
        post_text=str(payload.get("post_text", "")),
        post_url=str(payload.get("post_url", "")),
        post_id=str(payload.get("post_id", "")),
        root_comment_id=str(payload.get("root_comment_id", "")),
        source_links=tuple(str(item) for item in _list(links, "source_links")),
        privacy_checked=bool(payload.get("privacy_checked", False)),
        outcome_score=_optional_int(payload.get("outcome_score")),
        outcome_class=(
            OutcomeClass(str(payload["outcome_class"]))
            if payload.get("outcome_class") is not None
            else None
        ),
        outcome_notes=str(payload.get("outcome_notes", "")),
        user_rating=_optional_int(payload.get("user_rating")),
        what_worked=str(payload.get("what_worked", "")),
        what_failed=str(payload.get("what_failed", "")),
        next_test=str(payload.get("next_test", "")),
        closed_at=str(payload.get("closed_at", "")),
    )


def _optional_int(value: object) -> int | None:
    return None if value is None else int(str(value))


def _turn_record(payload: Mapping[str, Any]) -> TurnRecord:
    return TurnRecord(
        case_id=str(payload.get("case_id", "")),
        turn_id=str(payload.get("turn_id", "")),
        parent_turn_id=_optional_string(payload.get("parent_turn_id")),
        parent_confidence=(
            ParentConfidence(str(payload["parent_confidence"]))
            if payload.get("parent_confidence") is not None
            else None
        ),
        participant_ref=str(payload.get("participant_ref", "")),
        direction=TurnDirection(str(payload.get("direction", ""))),
        kind=TurnKind(str(payload.get("kind", ""))),
        state=TurnState(str(payload.get("state", ""))),
        exact_text=str(payload.get("exact_text", "")),
        post_id=str(payload.get("post_id", "")),
        root_comment_id=str(payload.get("root_comment_id", "")),
        reply_comment_id=_optional_string(payload.get("reply_comment_id")),
        exact_url=_optional_string(payload.get("exact_url")),
        url_supplied_at=_optional_string(payload.get("url_supplied_at")),
        observed_at=str(payload.get("observed_at", "")),
        notes=str(payload.get("notes", "")),
    )


def _pending_record(payload: Mapping[str, Any]) -> PendingSyncRecord:
    return PendingSyncRecord(
        operation=str(payload.get("operation", "")),
        target_file=str(payload.get("target_file", "")),
        target_sheet=str(payload.get("target_sheet", "")),
        case_id=str(payload.get("case_id", "")),
        turn_id=_optional_string(payload.get("turn_id")),
        expected_values=_mapping(payload.get("expected_values", {}), "expected_values"),
        failure=str(payload.get("failure", "")),
        last_verified_state=_mapping(
            payload.get("last_verified_state", {}), "last_verified_state"
        ),
        manual_version=str(payload.get("manual_version", "")),
        source_revision_state={
            str(key): str(value)
            for key, value in _mapping(
                payload.get("source_revision_state", {}), "source_revision_state"
            ).items()
        },
        required_reconciliation_action=str(payload.get("required_reconciliation_action", "")),
        created_at=str(payload.get("created_at", "")),
        resolved=bool(payload.get("resolved", False)),
    )


def _print(value: object) -> None:
    print(json.dumps(to_jsonable(value), ensure_ascii=False, indent=2, sort_keys=True))


def _doctor() -> dict[str, object]:
    root = Path.cwd()
    config_path = root / "config" / "drive-files.toml"
    checks: dict[str, bool] = {
        "git_repository": (root / ".git").exists(),
        "drive_config": config_path.exists(),
        "agents_bootstrap": (root / "AGENTS.md").exists(),
    }
    configured_signature = ""
    if config_path.exists():
        with config_path.open("rb") as stream:
            config = tomllib.load(stream)
        configured_signature = str(config["case_log"]["schema_signature"])
        checks["schema_signature"] = configured_signature == schema_signature().value
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "repository_schema_signature": schema_signature().value,
        "configured_schema_signature": configured_signature,
        "drive_connection": "runtime-managed; not exercised by the Python doctor",
        "writer_policy": "single writer; explicit approval; read-back required",
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dialogue-lab",
        description="Deterministic validation for the Israel Facebook Dialogue Lab",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="check local repository/configuration readiness")
    parse = sub.add_parser("parse-url", help="parse a Facebook URL without rewriting it")
    parse.add_argument("url")
    manual = sub.add_parser("manual-version", help="parse and validate Manual text or a file")
    manual.add_argument("text_or_file")
    schema = sub.add_parser("schema-check", help="validate an observed schema JSON file")
    schema.add_argument("schema_json")
    consistency = sub.add_parser("source-consistency", help="compare source revision states")
    consistency.add_argument("json_file")
    case_key = sub.add_parser("case-key", help="generate normalized canonical case identity")
    case_key.add_argument("--post-id", required=True)
    case_key.add_argument("--root-comment-id", required=True)
    case_id = sub.add_parser("next-case-id", help="allocate a date-local Case ID")
    case_id.add_argument("--date", required=True)
    case_id.add_argument("--existing", required=True)
    case_id.add_argument("--pending-sync")
    turn_id = sub.add_parser("next-turn-id", help="allocate a case-local Turn ID")
    turn_id.add_argument("--case-id", required=True)
    turn_id.add_argument("--existing", required=True)
    validate_case_parser = sub.add_parser("validate-case", help="validate a Case record")
    validate_case_parser.add_argument("json_file")
    validate_turn_parser = sub.add_parser("validate-turn", help="validate a Turn record")
    validate_turn_parser.add_argument("json_file")
    transition = sub.add_parser("validate-transition", help="validate a Case transition")
    transition.add_argument("json_file")
    graph = sub.add_parser("validate-parent-graph", help="validate a case-local parent graph")
    graph.add_argument("json_file")
    pending = sub.add_parser("pending-sync-check", help="fail while PENDING SYNC is unresolved")
    pending.add_argument("json_file")
    readback = sub.add_parser("verify-readback", help="compare expected and actual fields")
    readback.add_argument("--expected", required=True)
    readback.add_argument("--actual", required=True)
    receipt = sub.add_parser("migration-receipt", help="validate and render a migration receipt")
    receipt.add_argument("json_file")
    return parser


def _ids_from_json(value: object, key: str, case_id: str | None = None) -> list[str]:
    items = _list(value)
    output: list[str] = []
    for item in items:
        if isinstance(item, str):
            output.append(item)
        else:
            row = _mapping(item, "existing identifier row")
            if case_id is None or str(row.get("case_id", "")) == case_id:
                output.append(str(row.get(key, "")))
    return output


def _run(args: argparse.Namespace) -> object:
    command = str(args.command)
    if command == "doctor":
        result = _doctor()
        if not result["ok"]:
            raise DialogueLabError("local doctor checks failed")
        return result
    if command == "parse-url":
        return parse_facebook_url(str(args.url))
    if command == "manual-version":
        source = Path(str(args.text_or_file))
        text = source.read_text(encoding="utf-8") if source.is_file() else str(args.text_or_file)
        version, warnings = require_supported_manual(text)
        return {"version": str(version), "warnings": warnings}
    if command == "schema-check":
        signature = validate_schema(_mapping(_load_json(str(args.schema_json))))
        return {"compatible": True, "schema_signature": signature.value}
    if command == "source-consistency":
        payload = _mapping(_load_json(str(args.json_file)))
        start = {str(k): str(v) for k, v in _mapping(payload.get("operation_start", {})).items()}
        current = {str(k): str(v) for k, v in _mapping(payload.get("current", {})).items()}
        material_value = payload.get("material_sources")
        material = (
            [str(item) for item in _list(material_value, "material_sources")]
            if material_value is not None
            else None
        )
        return check_source_consistency(start, current, material_sources=material)
    if command == "case-key":
        return {"case_key": make_case_identity(args.post_id, args.root_comment_id).key}
    if command == "next-case-id":
        existing = _ids_from_json(_load_json(str(args.existing)), "case_id")
        pending_records: list[PendingSyncRecord] = []
        if args.pending_sync:
            pending_records = [
                _pending_record(_mapping(item))
                for item in _list(_load_json(str(args.pending_sync)))
            ]
        allocated = next_case_id(
            existing,
            on_date=date.fromisoformat(str(args.date)),
            pending_sync=pending_records,
        )
        return {"case_id": allocated}
    if command == "next-turn-id":
        existing = _ids_from_json(_load_json(str(args.existing)), "turn_id", str(args.case_id))
        return {"case_id": args.case_id, "turn_id": next_turn_id(existing)}
    if command == "validate-case":
        validate_case(_case_record(_mapping(_load_json(str(args.json_file)))))
        return {"valid": True}
    if command == "validate-turn":
        validate_turn(_turn_record(_mapping(_load_json(str(args.json_file)))))
        return {"valid": True}
    if command == "validate-transition":
        payload = _mapping(_load_json(str(args.json_file)))
        validate_transition(
            LifecycleTransition(
                CaseStatus(str(payload.get("from_status", ""))),
                CaseStatus(str(payload.get("to_status", ""))),
                str(payload.get("reason", "")),
            )
        )
        return {"valid": True}
    if command == "validate-parent-graph":
        turns = [_turn_record(_mapping(item)) for item in _list(_load_json(str(args.json_file)))]
        validate_parent_graph(turns)
        return {"valid": True, "turn_count": len(turns)}
    if command == "pending-sync-check":
        records = [
            _pending_record(_mapping(item)) for item in _list(_load_json(str(args.json_file)))
        ]
        require_no_pending_sync(records)
        return {"clear": True}
    if command == "verify-readback":
        expected = _mapping(_load_json(str(args.expected)))
        actual = _mapping(_load_json(str(args.actual)))
        verification = verify_readback(expected, actual)
        if not verification.succeeded:
            raise DialogueLabError(
                "read-back verification failed: " + "; ".join(verification.mismatches)
            )
        return verification
    if command == "migration-receipt":
        receipt = migration_receipt_from_mapping(_mapping(_load_json(str(args.json_file))))
        return json.loads(render_migration_receipt(receipt))
    raise DialogueLabError(f"unknown command: {command}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        _print(_run(args))
        return 0
    except (DialogueLabError, OSError, ValueError, KeyError) as error:
        category = getattr(error, "category", "input_error")
        print(json.dumps({"ok": False, "error": str(error), "category": category}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
