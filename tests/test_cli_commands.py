import json
from pathlib import Path

import pytest

from dialogue_lab.cli import main
from dialogue_lab.enums import CaseStatus, TurnDirection, TurnState
from dialogue_lab.models import to_jsonable
from dialogue_lab.schema import expected_schema_payload
from tests.helpers import make_case, make_reply, make_turn


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(to_jsonable(value), ensure_ascii=False), encoding="utf-8")
    return path


def _run_ok(capsys: pytest.CaptureFixture[str], *args: str) -> dict[str, object]:
    assert main(list(args)) == 0
    result = json.loads(capsys.readouterr().out)
    assert isinstance(result, dict)
    return result


def test_all_required_cli_commands_smoke(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run_ok(capsys, "doctor")["ok"] is True
    manual = tmp_path / "manual.txt"
    manual.write_text("Version 2.7 — synthetic", encoding="utf-8")
    assert _run_ok(capsys, "manual-version", str(manual))["version"] == "2.7"

    expected = expected_schema_payload()
    headers = expected["headers"]
    assert isinstance(headers, dict)
    observed = {
        "sheets": {
            "Cases": headers["Cases"],
            "Turns": headers["Turns"],
            "Data Dictionary": [],
            "Strategy Taxonomy": [],
            "Dashboard": [],
        },
        "enums": expected["enums"],
        "dashboard_formulas": expected["essential_dashboard_formulas"],
    }
    schema_path = _write(tmp_path / "schema.json", observed)
    assert _run_ok(capsys, "schema-check", str(schema_path))["compatible"] is True

    consistency_path = _write(
        tmp_path / "consistency.json",
        {"operation_start": {"manual": "r1"}, "current": {"manual": "r1"}},
    )
    assert _run_ok(capsys, "source-consistency", str(consistency_path))["consistent"] is True
    assert _run_ok(
        capsys, "case-key", "--post-id", "123", "--root-comment-id", "456"
    )["case_key"] == "facebook:123:456"

    ids_path = _write(tmp_path / "case-ids.json", ["CASE-20260717-001"])
    assert _run_ok(
        capsys,
        "next-case-id",
        "--date",
        "2026-07-17",
        "--existing",
        str(ids_path),
    )["case_id"] == "CASE-20260717-002"
    turns_path = _write(
        tmp_path / "turn-ids.json",
        [{"case_id": "CASE-20260717-001", "turn_id": "T001"}],
    )
    assert _run_ok(
        capsys,
        "next-turn-id",
        "--case-id",
        "CASE-20260717-001",
        "--existing",
        str(turns_path),
    )["turn_id"] == "T002"

    case_path = _write(tmp_path / "case.json", make_case())
    assert _run_ok(capsys, "validate-case", str(case_path))["valid"] is True
    turn = make_turn()
    turn_path = _write(tmp_path / "turn.json", turn)
    assert _run_ok(capsys, "validate-turn", str(turn_path))["valid"] is True
    transition_path = _write(
        tmp_path / "transition.json",
        {
            "from_status": CaseStatus.POSTED,
            "to_status": CaseStatus.ACTIVE_EXCHANGE,
            "reason": "new turn",
        },
    )
    assert _run_ok(capsys, "validate-transition", str(transition_path))["valid"] is True
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
    assert _run_ok(capsys, "validate-parent-graph", str(graph_path))["turn_count"] == 2
    pending_path = _write(tmp_path / "pending.json", [])
    assert _run_ok(capsys, "pending-sync-check", str(pending_path))["clear"] is True

    expected_path = _write(tmp_path / "expected.json", {"Turn ID": "T001"})
    actual_path = _write(tmp_path / "actual.json", {"Turn ID": "T001"})
    assert _run_ok(
        capsys,
        "verify-readback",
        "--expected",
        str(expected_path),
        "--actual",
        str(actual_path),
    )["succeeded"] is True

    receipt_path = Path(__file__).parents[1] / "docs" / "migration-receipt.json.example"
    receipt = _run_ok(capsys, "migration-receipt", str(receipt_path))
    assert receipt["manual_version"] == "2.7"
