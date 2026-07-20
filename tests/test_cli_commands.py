import json
from pathlib import Path

import pytest

from dialogue_lab.cli import main
from dialogue_lab.enums import CaseStatus, OutcomeClass, TurnDirection, TurnState
from dialogue_lab.models import to_jsonable
from tests.helpers import make_case, make_reply, make_turn


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(to_jsonable(value), ensure_ascii=False), encoding="utf-8")
    return path


def _run_ok(capsys: pytest.CaptureFixture[str], *args: str) -> object:
    assert main(list(args)) == 0
    return json.loads(capsys.readouterr().out)


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return value


def test_transactional_case_cli_lifecycle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "canonical.sqlite3"
    db = ("--database", str(database))
    initialized = _as_dict(_run_ok(capsys, *db, "db-init", "--approved"))
    assert initialized["integrity"] == "ok"
    assert _as_dict(_run_ok(capsys, *db, "doctor"))["ok"] is True

    case_payload = _as_dict(to_jsonable(make_case()))
    case_payload.pop("case_id")
    turn_payload = _as_dict(to_jsonable(make_turn()))
    intake_path = _write(
        tmp_path / "intake.json",
        {"case": case_payload, "turns": [turn_payload]},
    )
    intake = _as_dict(
        _run_ok(
            capsys,
            *db,
            "case-intake",
            str(intake_path),
            "--date",
            "2026-07-17",
            "--approved",
        )
    )
    assert intake == {
        "created": True,
        "case_id": "CASE-20260717-001",
        "turn_count": 1,
    }

    duplicate = _as_dict(
        _run_ok(
            capsys,
            *db,
            "case-intake",
            str(intake_path),
            "--date",
            "2026-07-17",
            "--approved",
        )
    )
    assert duplicate["duplicate"] is True
    assert duplicate["case_id"] == "CASE-20260717-001"

    open_cases = _run_ok(capsys, *db, "case-list-open")
    assert open_cases == [
        {
            "case_id": "CASE-20260717-001",
            "status": "Posted",
            "exact_permalink": case_payload["post_url"],
        }
    ]
    found = _as_dict(
        _run_ok(
            capsys,
            *db,
            "case-find",
            "--post-id",
            "123",
            "--root-comment-id",
            "456",
        )
    )
    assert found["case_id"] == "CASE-20260717-001"

    followup = make_reply(
        "ignored",
        "T001",
        observed_at="2026-07-17 11:00",
        exact_text="Synthetic follow-up.",
    )
    followup_path = _write(tmp_path / "followup.json", followup)
    followup_receipt = _as_dict(
        _run_ok(
            capsys,
            *db,
            "case-followup",
            "--case-id",
            "CASE-20260717-001",
            str(followup_path),
            "--approved",
        )
    )
    assert followup_receipt["turn_id"] == "T002"
    assert followup_receipt["status"] == "Active Exchange"

    posted = make_reply(
        "ignored",
        "T002",
        participant_ref="USER",
        direction=TurnDirection.OUTGOING,
        state=TurnState.POSTED,
        exact_text="Exact published reply.",
        observed_at="2026-07-17 12:00",
    )
    posting_path = _write(tmp_path / "posting.json", posted)
    posting_receipt = _as_dict(
        _run_ok(
            capsys,
            *db,
            "case-record-posting",
            "--case-id",
            "CASE-20260717-001",
            str(posting_path),
            "--approved",
        )
    )
    assert posting_receipt["turn_id"] == "T003"
    assert posting_receipt["readback"] == "verified"

    close_path = _write(
        tmp_path / "close.json",
        {
            "status": CaseStatus.CLOSED_SUBSTANTIVE,
            "updated_at": "2026-07-18 10:00",
            "outcome_score": 3,
            "outcome_class": OutcomeClass.SUBSTANTIVE_ENGAGEMENT,
            "outcome_notes": "Observable exchange of reasons.",
            "what_worked": "Narrow question.",
            "what_failed": "Long setup.",
            "next_test": "Lead with the narrow question.",
            "closed_at": "2026-07-18 10:00",
            "reason": "explicit closeout",
        },
    )
    close_receipt = _as_dict(
        _run_ok(
            capsys,
            *db,
            "case-close",
            "--case-id",
            "CASE-20260717-001",
            str(close_path),
            "--approved",
        )
    )
    assert close_receipt["status"] == "Closed - Substantive"
    assert _run_ok(capsys, *db, "case-list-open") == []
    dataset = _as_dict(_run_ok(capsys, *db, "strategy-dataset"))
    assert len(dataset["cases"]) == 1  # type: ignore[arg-type]
    assert len(dataset["turns"]["CASE-20260717-001"]) == 3  # type: ignore[index]


def test_pure_validation_commands_and_migration_receipt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _as_dict(
        _run_ok(
            capsys,
            "case-key",
            "--post-id",
            "123",
            "--root-comment-id",
            "456",
        )
    )["case_key"] == "facebook:123:456"

    ids_path = _write(tmp_path / "case-ids.json", ["CASE-20260717-001"])
    assert _as_dict(
        _run_ok(
            capsys,
            "next-case-id",
            "--date",
            "2026-07-17",
            "--existing",
            str(ids_path),
        )
    )["case_id"] == "CASE-20260717-002"
    turns_path = _write(
        tmp_path / "turn-ids.json",
        [{"case_id": "CASE-20260717-001", "turn_id": "T001"}],
    )
    assert _as_dict(
        _run_ok(
            capsys,
            "next-turn-id",
            "--case-id",
            "CASE-20260717-001",
            "--existing",
            str(turns_path),
        )
    )["turn_id"] == "T002"

    case_path = _write(tmp_path / "case.json", make_case())
    assert _as_dict(_run_ok(capsys, "validate-case", str(case_path)))["valid"] is True
    turn = make_turn()
    turn_path = _write(tmp_path / "turn.json", turn)
    assert _as_dict(_run_ok(capsys, "validate-turn", str(turn_path)))["valid"] is True
    transition_path = _write(
        tmp_path / "transition.json",
        {
            "from_status": CaseStatus.POSTED,
            "to_status": CaseStatus.ACTIVE_EXCHANGE,
            "reason": "new turn",
        },
    )
    assert _as_dict(
        _run_ok(capsys, "validate-transition", str(transition_path))
    )["valid"] is True
    graph_path = _write(
        tmp_path / "graph.json",
        [
            turn,
            make_reply(
                "T002",
                "T001",
                participant_ref="USER",
                direction=TurnDirection.OUTGOING,
                state=TurnState.POSTED,
            ),
        ],
    )
    assert _as_dict(
        _run_ok(capsys, "validate-parent-graph", str(graph_path))
    )["turn_count"] == 2

    expected_path = _write(tmp_path / "expected.json", {"turn_id": "T001"})
    actual_path = _write(tmp_path / "actual.json", {"turn_id": "T001"})
    assert _as_dict(
        _run_ok(
            capsys,
            "verify-readback",
            "--expected",
            str(expected_path),
            "--actual",
            str(actual_path),
        )
    )["succeeded"] is True

    receipt_path = Path(__file__).parents[1] / "docs" / "migration-receipt.json.example"
    receipt = _as_dict(_run_ok(capsys, "migration-receipt", str(receipt_path)))
    assert receipt["database_schema_version"] == 1


def test_write_command_rejects_missing_approval(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "canonical.sqlite3"
    assert main(["--database", str(database), "db-init"]) == 2
    error = json.loads(capsys.readouterr().err)
    assert error["category"] == "write_safety_error"
    assert not database.exists()
