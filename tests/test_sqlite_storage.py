import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from dialogue_lab.enums import CaseStatus, OutcomeClass, TurnDirection, TurnState
from dialogue_lab.errors import DialogueLabError, StorageError, WriteSafetyError
from dialogue_lab.storage import SQLiteStore
from dialogue_lab.validation import validate_case
from tests.helpers import make_case, make_reply, make_turn


def test_database_initialization_requires_approval_and_reports_integrity(
    tmp_path: Path,
) -> None:
    store = SQLiteStore(tmp_path / "dialogue-lab.sqlite3")
    with pytest.raises(WriteSafetyError, match="approval"):
        store.initialize(approved=False)

    status = store.initialize(approved=True)
    assert status["integrity"] == "ok"
    assert status["schema_version"] == 1
    assert status["case_count"] == 0


def test_case_creation_is_atomic_unique_and_read_back(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "dialogue-lab.sqlite3")
    store.initialize(approved=True)
    case = make_case()
    turn = make_turn()

    receipt = store.create_case(case, [turn], approved=True)
    assert receipt == {
        "created": True,
        "case_id": "CASE-20260717-001",
        "turn_count": 1,
    }
    assert store.get_case(case.case_id) == case
    assert store.get_turns(case.case_id) == [turn]

    duplicate = make_case(case_id="CASE-20260717-002")
    with pytest.raises(StorageError, match="UNIQUE"):
        store.create_case(duplicate, [], approved=True)
    assert store.status()["case_count"] == 1


def test_failed_import_rolls_back_every_row(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "dialogue-lab.sqlite3")
    store.initialize(approved=True)
    first = make_case(case_id="CASE-20260717-001")
    duplicate_identity = make_case(case_id="CASE-20260717-002")

    with pytest.raises(StorageError, match="UNIQUE"):
        store.import_records([first, duplicate_identity], [], approved=True)

    assert store.status()["case_count"] == 0


def test_schema_version_mismatch_blocks_reads(tmp_path: Path) -> None:
    path = tmp_path / "dialogue-lab.sqlite3"
    store = SQLiteStore(path)
    store.initialize(approved=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version = 99")

    with pytest.raises(StorageError, match="schema version mismatch"):
        store.status()


def test_initialization_refuses_an_unrelated_database(tmp_path: Path) -> None:
    path = tmp_path / "unrelated.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unrelated(value TEXT)")

    with pytest.raises(StorageError, match="non-empty unversioned"):
        SQLiteStore(path).initialize(approved=True)


def test_followup_updates_status_and_verifies_committed_turn(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "dialogue-lab.sqlite3")
    store.initialize(approved=True)
    case = make_case()
    first = make_turn()
    store.create_case(case, [first], approved=True)
    followup = make_reply(
        "T002",
        "T001",
        observed_at="2026-07-17 11:00",
    )

    receipt = store.add_turn(
        followup,
        target_status=CaseStatus.ACTIVE_EXCHANGE,
        updated_at=followup.observed_at,
        reason="incoming public turn",
        replace_draft_id=None,
        approved=True,
    )

    assert receipt["readback"] == "verified"
    assert store.get_case(case.case_id).status is CaseStatus.ACTIVE_EXCHANGE
    assert store.get_turns(case.case_id)[-1] == followup


def test_posting_retires_named_draft_in_same_transaction(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "dialogue-lab.sqlite3")
    store.initialize(approved=True)
    case = make_case(status=CaseStatus.ACTIVE_EXCHANGE)
    first = make_turn()
    draft = make_reply(
        "T002",
        "T001",
        participant_ref="USER",
        direction=TurnDirection.OUTGOING,
        state=TurnState.DRAFT,
    )
    store.create_case(case, [first, draft], approved=True)
    posted = make_reply(
        "T003",
        "T001",
        participant_ref="USER",
        direction=TurnDirection.OUTGOING,
        state=TurnState.POSTED,
        exact_text="Exact published wording.",
        observed_at="2026-07-17 12:00",
    )

    store.add_turn(
        posted,
        target_status=CaseStatus.ACTIVE_EXCHANGE,
        updated_at=posted.observed_at,
        reason="posting confirmed",
        replace_draft_id="T002",
        approved=True,
    )

    turns = store.get_turns(case.case_id)
    assert turns[1].state is TurnState.REPLACED
    assert turns[2] == posted


def test_close_case_writes_only_validated_outcome_and_reads_back(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "dialogue-lab.sqlite3")
    store.initialize(approved=True)
    case = make_case(status=CaseStatus.ACTIVE_EXCHANGE)
    store.create_case(case, [make_turn()], approved=True)
    closed = replace(
        case,
        status=CaseStatus.CLOSED_SUBSTANTIVE,
        updated_at="2026-07-18 10:00",
        outcome_score=3,
        outcome_class=OutcomeClass.SUBSTANTIVE_ENGAGEMENT,
        outcome_notes="Observable exchange of reasons.",
        what_worked="Narrow question.",
        what_failed="Long setup.",
        next_test="Lead with the narrow question.",
        closed_at="2026-07-18 10:00",
    )

    receipt = store.close_case(closed, reason="explicit closeout", approved=True)

    assert receipt["readback"] == "verified"
    assert store.get_case(case.case_id) == closed


def test_open_case_requires_and_returns_exact_comment_permalink(tmp_path: Path) -> None:
    invalid = make_case(post_url="https://www.facebook.com/example/posts/123")
    with pytest.raises(DialogueLabError, match="comment or reply"):
        validate_case(invalid)

    store = SQLiteStore(tmp_path / "dialogue-lab.sqlite3")
    store.initialize(approved=True)
    case = make_case(
        post_url=(
            "https://www.facebook.com/example/posts/123?comment_id=456"
            "&__cft__[0]=tracking#comment"
        )
    )
    store.create_case(case, [], approved=True)
    assert store.list_open_summaries() == [
        {
            "case_id": case.case_id,
            "status": "Posted",
            "exact_permalink": case.post_url,
        }
    ]


def test_backup_is_consistent_and_never_overwrites(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "dialogue-lab.sqlite3")
    store.initialize(approved=True)
    store.create_case(make_case(), [], approved=True)
    destination = tmp_path / "backups" / "snapshot.sqlite3"

    store.backup(destination, approved=True)
    assert SQLiteStore(destination).status()["case_count"] == 1
    with pytest.raises(StorageError, match="already exists"):
        store.backup(destination, approved=True)
