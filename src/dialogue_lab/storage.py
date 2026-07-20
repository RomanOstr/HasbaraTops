"""Transactional SQLite storage for canonical Dialogue Lab case state.

All mutations require an explicit approval flag, run inside an immediate
transaction, and are read back after commit. The caller supplies the database
path; this module never discovers credentials, contacts a network service, or
writes outside that path and explicitly requested backup destinations.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import replace
from pathlib import Path

from .enums import (
    CaseStatus,
    OutcomeClass,
    ParentConfidence,
    TurnDirection,
    TurnKind,
    TurnState,
)
from .errors import StorageError, WriteSafetyError
from .facebook_url import parse_facebook_url
from .lifecycle import CLOSED_STATUSES, validate_transition
from .models import CaseRecord, LifecycleTransition, TurnRecord, to_jsonable
from .parent_graph import validate_parent_graph
from .readback import verify_readback
from .schema import CASE_FIELDS, SCHEMA_VERSION, TURN_FIELDS, schema_signature
from .validation import validate_case, validate_turn


def _sql_enum(values: Iterable[str]) -> str:
    return ", ".join("'" + value.replace("'", "''") + "'" for value in values)


_STATUS_SQL = _sql_enum(item.value for item in CaseStatus)
_OUTCOME_SQL = _sql_enum(item.value for item in OutcomeClass)
_CONFIDENCE_SQL = _sql_enum(item.value for item in ParentConfidence)
_DIRECTION_SQL = _sql_enum(item.value for item in TurnDirection)
_KIND_SQL = _sql_enum(item.value for item in TurnKind)
_STATE_SQL = _sql_enum(item.value for item in TurnState)
_SCHEMA_SIGNATURE = schema_signature().value

_SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS storage_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    case_title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ({_STATUS_SQL})),
    topic TEXT NOT NULL,
    post_text TEXT NOT NULL,
    post_url TEXT NOT NULL,
    post_id TEXT NOT NULL,
    root_comment_id TEXT NOT NULL,
    source_links TEXT NOT NULL DEFAULT '[]',
    privacy_checked INTEGER NOT NULL CHECK (privacy_checked IN (0, 1)),
    outcome_score INTEGER CHECK (outcome_score BETWEEN 0 AND 5),
    outcome_class TEXT CHECK (outcome_class IS NULL OR outcome_class IN ({_OUTCOME_SQL})),
    outcome_notes TEXT NOT NULL DEFAULT '',
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    what_worked TEXT NOT NULL DEFAULT '',
    what_failed TEXT NOT NULL DEFAULT '',
    next_test TEXT NOT NULL DEFAULT '',
    closed_at TEXT NOT NULL DEFAULT '',
    UNIQUE (post_id, root_comment_id)
);

CREATE TABLE IF NOT EXISTS turns (
    case_id TEXT NOT NULL,
    turn_id TEXT NOT NULL,
    parent_turn_id TEXT,
    parent_confidence TEXT CHECK (
        parent_confidence IS NULL OR parent_confidence IN ({_CONFIDENCE_SQL})
    ),
    participant_ref TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ({_DIRECTION_SQL})),
    kind TEXT NOT NULL CHECK (kind IN ({_KIND_SQL})),
    state TEXT NOT NULL CHECK (state IN ({_STATE_SQL})),
    exact_text TEXT NOT NULL,
    post_id TEXT NOT NULL,
    root_comment_id TEXT NOT NULL,
    reply_comment_id TEXT,
    exact_url TEXT,
    url_supplied_at TEXT,
    observed_at TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (case_id, turn_id),
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE RESTRICT,
    FOREIGN KEY (case_id, parent_turn_id) REFERENCES turns(case_id, turn_id)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS turns_case_observed_idx
    ON turns(case_id, observed_at, turn_id);
INSERT INTO storage_metadata(key, value)
    VALUES ('schema_signature', '{_SCHEMA_SIGNATURE}')
    ON CONFLICT(key) DO NOTHING;
PRAGMA user_version = {SCHEMA_VERSION};
"""


def _require_approval(approved: bool) -> None:
    if not approved:
        raise WriteSafetyError("canonical SQLite writes require explicit approval")


def _case_values(record: CaseRecord) -> dict[str, object]:
    return {
        "case_id": record.case_id,
        "case_title": record.case_title,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "status": record.status.value,
        "topic": record.topic,
        "post_text": record.post_text,
        "post_url": record.post_url,
        "post_id": record.post_id,
        "root_comment_id": record.root_comment_id,
        "source_links": json.dumps(list(record.source_links), ensure_ascii=False),
        "privacy_checked": int(record.privacy_checked),
        "outcome_score": record.outcome_score,
        "outcome_class": record.outcome_class.value if record.outcome_class else None,
        "outcome_notes": record.outcome_notes,
        "user_rating": record.user_rating,
        "what_worked": record.what_worked,
        "what_failed": record.what_failed,
        "next_test": record.next_test,
        "closed_at": record.closed_at,
    }


def _turn_values(record: TurnRecord) -> dict[str, object]:
    return {
        "case_id": record.case_id,
        "turn_id": record.turn_id,
        "parent_turn_id": record.parent_turn_id,
        "parent_confidence": (
            record.parent_confidence.value if record.parent_confidence else None
        ),
        "participant_ref": record.participant_ref,
        "direction": record.direction.value,
        "kind": record.kind.value,
        "state": record.state.value,
        "exact_text": record.exact_text,
        "post_id": record.post_id,
        "root_comment_id": record.root_comment_id,
        "reply_comment_id": record.reply_comment_id,
        "exact_url": record.exact_url,
        "url_supplied_at": record.url_supplied_at,
        "observed_at": record.observed_at,
        "notes": record.notes,
    }


def _case_from_row(row: sqlite3.Row) -> CaseRecord:
    raw_links = json.loads(str(row["source_links"]))
    if not isinstance(raw_links, list):
        raise StorageError(f"invalid source_links JSON for {row['case_id']}")
    return CaseRecord(
        case_id=str(row["case_id"]),
        case_title=str(row["case_title"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        status=CaseStatus(str(row["status"])),
        topic=str(row["topic"]),
        post_text=str(row["post_text"]),
        post_url=str(row["post_url"]),
        post_id=str(row["post_id"]),
        root_comment_id=str(row["root_comment_id"]),
        source_links=tuple(str(item) for item in raw_links),
        privacy_checked=bool(row["privacy_checked"]),
        outcome_score=(int(row["outcome_score"]) if row["outcome_score"] is not None else None),
        outcome_class=(
            OutcomeClass(str(row["outcome_class"]))
            if row["outcome_class"] is not None
            else None
        ),
        outcome_notes=str(row["outcome_notes"]),
        user_rating=(int(row["user_rating"]) if row["user_rating"] is not None else None),
        what_worked=str(row["what_worked"]),
        what_failed=str(row["what_failed"]),
        next_test=str(row["next_test"]),
        closed_at=str(row["closed_at"]),
    )


def _turn_from_row(row: sqlite3.Row) -> TurnRecord:
    return TurnRecord(
        case_id=str(row["case_id"]),
        turn_id=str(row["turn_id"]),
        parent_turn_id=(str(row["parent_turn_id"]) if row["parent_turn_id"] else None),
        parent_confidence=(
            ParentConfidence(str(row["parent_confidence"]))
            if row["parent_confidence"] is not None
            else None
        ),
        participant_ref=str(row["participant_ref"]),
        direction=TurnDirection(str(row["direction"])),
        kind=TurnKind(str(row["kind"])),
        state=TurnState(str(row["state"])),
        exact_text=str(row["exact_text"]),
        post_id=str(row["post_id"]),
        root_comment_id=str(row["root_comment_id"]),
        reply_comment_id=(
            str(row["reply_comment_id"]) if row["reply_comment_id"] is not None else None
        ),
        exact_url=str(row["exact_url"]) if row["exact_url"] is not None else None,
        url_supplied_at=(
            str(row["url_supplied_at"]) if row["url_supplied_at"] is not None else None
        ),
        observed_at=str(row["observed_at"]),
        notes=str(row["notes"]),
    )


class SQLiteStore:
    """Narrow canonical storage API; no generic SQL execution is exposed."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def _connect(
        self, *, require_exists: bool = True, writable: bool = False
    ) -> sqlite3.Connection:
        if require_exists and not self.path.is_file():
            raise StorageError(f"database does not exist: {self.path}")
        target = self.path if writable else f"{self.path.as_uri()}?mode=ro"
        connection = sqlite3.connect(
            target,
            timeout=5.0,
            isolation_level=None,
            uri=not writable,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def initialize(self, *, approved: bool) -> Mapping[str, object]:
        """Create or verify the schema without replacing an existing database."""
        _require_approval(approved)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect(require_exists=False, writable=True) as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version not in {0, SCHEMA_VERSION}:
                raise StorageError(
                    f"unsupported database schema version: {version}; expected {SCHEMA_VERSION}"
                )
            if version == 0:
                tables = connection.execute(
                    """SELECT name FROM sqlite_master
                    WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"""
                ).fetchall()
                if tables:
                    raise StorageError("refusing to initialize a non-empty unversioned database")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA_SQL)
        return self.status()

    def status(self) -> Mapping[str, object]:
        with self._connect() as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version != SCHEMA_VERSION:
                raise StorageError(
                    f"database schema version mismatch: {version}; expected {SCHEMA_VERSION}"
                )
            signature_row = connection.execute(
                "SELECT value FROM storage_metadata WHERE key = 'schema_signature'"
            ).fetchone()
            actual_signature = str(signature_row["value"]) if signature_row else ""
            if actual_signature != _SCHEMA_SIGNATURE:
                raise StorageError("database schema signature mismatch")
            case_columns = tuple(
                str(row["name"]) for row in connection.execute("PRAGMA table_info(cases)")
            )
            turn_columns = tuple(
                str(row["name"]) for row in connection.execute("PRAGMA table_info(turns)")
            )
            if case_columns != CASE_FIELDS or turn_columns != TURN_FIELDS:
                raise StorageError("database table columns do not match the canonical schema")
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            case_count = int(connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0])
            turn_count = int(connection.execute("SELECT COUNT(*) FROM turns").fetchone()[0])
        if integrity != "ok" or foreign_keys:
            raise StorageError("database integrity check failed")
        return {
            "ok": True,
            "schema_version": version,
            "schema_signature": actual_signature,
            "integrity": integrity,
            "case_count": case_count,
            "turn_count": turn_count,
        }

    def backup(self, destination: Path, *, approved: bool) -> Mapping[str, object]:
        """Create a verified backup, never overwrite, and remove partial output on failure."""
        _require_approval(approved)
        target = destination.resolve()
        if target.exists():
            raise StorageError(f"backup destination already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect() as source, sqlite3.connect(target) as backup:
                source.backup(backup)
            status = SQLiteStore(target).status()
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return {"ok": True, "backup": str(target), "database": status}

    def case_ids(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute("SELECT case_id FROM cases ORDER BY case_id").fetchall()
        return [str(row["case_id"]) for row in rows]

    def turn_ids(self, case_id: str) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT turn_id FROM turns WHERE case_id = ? ORDER BY turn_id", (case_id,)
            ).fetchall()
        return [str(row["turn_id"]) for row in rows]

    def _get_case(self, connection: sqlite3.Connection, case_id: str) -> CaseRecord:
        row = connection.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        if row is None:
            raise StorageError(f"case not found: {case_id}")
        return _case_from_row(row)

    def _get_turns(self, connection: sqlite3.Connection, case_id: str) -> list[TurnRecord]:
        rows = connection.execute(
            "SELECT * FROM turns WHERE case_id = ? ORDER BY turn_id", (case_id,)
        ).fetchall()
        return [_turn_from_row(row) for row in rows]

    def get_case(self, case_id: str) -> CaseRecord:
        with self._connect() as connection:
            return self._get_case(connection, case_id)

    def get_turns(self, case_id: str) -> list[TurnRecord]:
        with self._connect() as connection:
            self._get_case(connection, case_id)
            return self._get_turns(connection, case_id)

    def find_case(self, post_id: str, root_comment_id: str) -> CaseRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM cases WHERE post_id = ? AND root_comment_id = ?",
                (post_id, root_comment_id),
            ).fetchone()
        return _case_from_row(row) if row is not None else None

    def list_open_summaries(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM cases ORDER BY case_id").fetchall()
        output: list[dict[str, str]] = []
        for row in rows:
            case = _case_from_row(row)
            if case.status in CLOSED_STATUSES:
                continue
            parsed = parse_facebook_url(case.post_url)
            if parsed.root_comment_id is None and parsed.reply_comment_id is None:
                raise StorageError(
                    f"open case lacks a comment or reply permalink: {case.case_id}"
                )
            output.append(
                {
                    "case_id": case.case_id,
                    "status": case.status.value,
                    "exact_permalink": parsed.original_url,
                }
            )
        return output

    def strategy_dataset(self) -> Mapping[str, object]:
        with self._connect() as connection:
            cases = [
                _case_from_row(row)
                for row in connection.execute("SELECT * FROM cases ORDER BY case_id")
                if CaseStatus(str(row["status"])) in CLOSED_STATUSES
            ]
            turns = {
                case.case_id: self._get_turns(connection, case.case_id) for case in cases
            }
        return {"cases": cases, "turns": turns}

    @staticmethod
    def _insert_case(connection: sqlite3.Connection, record: CaseRecord) -> None:
        connection.execute(
            """INSERT INTO cases VALUES (
                :case_id, :case_title, :created_at, :updated_at, :status, :topic,
                :post_text, :post_url, :post_id, :root_comment_id, :source_links,
                :privacy_checked, :outcome_score, :outcome_class, :outcome_notes,
                :user_rating, :what_worked, :what_failed, :next_test, :closed_at
            )""",
            _case_values(record),
        )

    @staticmethod
    def _insert_turn(connection: sqlite3.Connection, record: TurnRecord) -> None:
        connection.execute(
            """INSERT INTO turns VALUES (
                :case_id, :turn_id, :parent_turn_id, :parent_confidence,
                :participant_ref, :direction, :kind, :state, :exact_text, :post_id,
                :root_comment_id, :reply_comment_id, :exact_url, :url_supplied_at,
                :observed_at, :notes
            )""",
            _turn_values(record),
        )

    @staticmethod
    def _validate_bundle(cases: list[CaseRecord], turns: list[TurnRecord]) -> None:
        by_case = {case.case_id: case for case in cases}
        if len(by_case) != len(cases):
            raise StorageError("duplicate Case IDs in write payload")
        grouped: dict[str, list[TurnRecord]] = defaultdict(list)
        for case in cases:
            validate_case(case)
        for turn in turns:
            validate_turn(turn)
            parent_case = by_case.get(turn.case_id)
            if parent_case is None:
                raise StorageError(f"turn references missing Case: {turn.case_id}")
            if (turn.post_id, turn.root_comment_id) != (
                parent_case.post_id,
                parent_case.root_comment_id,
            ):
                raise StorageError(f"turn identity conflicts with Case: {turn.turn_id}")
            grouped[turn.case_id].append(turn)
        for case_turns in grouped.values():
            validate_parent_graph(case_turns)

    def import_records(
        self, cases: list[CaseRecord], turns: list[TurnRecord], *, approved: bool
    ) -> Mapping[str, object]:
        """Atomically import a validated snapshot into an empty database."""
        _require_approval(approved)
        self._validate_bundle(cases, turns)
        try:
            with self._connect(writable=True) as connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = int(connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0])
                existing += int(connection.execute("SELECT COUNT(*) FROM turns").fetchone()[0])
                if existing:
                    raise StorageError("database import requires empty cases and turns tables")
                for case in cases:
                    self._insert_case(connection, case)
                for turn in turns:
                    self._insert_turn(connection, turn)
                connection.commit()
        except sqlite3.Error as error:
            raise StorageError(f"database import failed: {error}") from error
        status = self.status()
        if status["case_count"] != len(cases) or status["turn_count"] != len(turns):
            raise StorageError("database import read-back count mismatch")
        for case in cases:
            if self.get_case(case.case_id) != case:
                raise StorageError(f"database import Case read-back mismatch: {case.case_id}")
        expected_turns: dict[str, list[TurnRecord]] = defaultdict(list)
        for turn in turns:
            expected_turns[turn.case_id].append(turn)
        for case_id, case_turns in expected_turns.items():
            if self.get_turns(case_id) != sorted(case_turns, key=lambda item: item.turn_id):
                raise StorageError(f"database import Turn read-back mismatch: {case_id}")
        return status

    def create_case(
        self, case: CaseRecord, turns: list[TurnRecord], *, approved: bool
    ) -> Mapping[str, object]:
        """Atomically create one Case and its initial public-turn graph."""
        _require_approval(approved)
        self._validate_bundle([case], turns)
        try:
            with self._connect(writable=True) as connection:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_case(connection, case)
                for turn in turns:
                    self._insert_turn(connection, turn)
                connection.commit()
        except sqlite3.Error as error:
            raise StorageError(f"case creation failed: {error}") from error
        actual_case = self.get_case(case.case_id)
        actual_turns = self.get_turns(case.case_id)
        if actual_case != case or actual_turns != sorted(turns, key=lambda item: item.turn_id):
            raise StorageError("case creation read-back mismatch")
        return {"created": True, "case_id": case.case_id, "turn_count": len(turns)}

    def add_turn(
        self,
        turn: TurnRecord,
        *,
        target_status: CaseStatus,
        updated_at: str,
        reason: str,
        replace_draft_id: str | None,
        approved: bool,
    ) -> Mapping[str, object]:
        """Atomically append one turn, optionally retire a Draft, and update Case state."""
        _require_approval(approved)
        validate_turn(turn)
        try:
            with self._connect(writable=True) as connection:
                connection.execute("BEGIN IMMEDIATE")
                case = self._get_case(connection, turn.case_id)
                if (turn.post_id, turn.root_comment_id) != (
                    case.post_id,
                    case.root_comment_id,
                ):
                    raise StorageError(f"turn identity conflicts with Case: {turn.turn_id}")
                validate_transition(LifecycleTransition(case.status, target_status, reason))
                existing_turns = self._get_turns(connection, turn.case_id)
                if replace_draft_id is not None:
                    draft = next(
                        (item for item in existing_turns if item.turn_id == replace_draft_id),
                        None,
                    )
                    if (
                        draft is None
                        or draft.direction is not TurnDirection.OUTGOING
                        or draft.state is not TurnState.DRAFT
                    ):
                        raise StorageError(
                            f"replacement target is not an Outgoing Draft: {replace_draft_id}"
                        )
                    connection.execute(
                        "UPDATE turns SET state = ? WHERE case_id = ? AND turn_id = ?",
                        (TurnState.REPLACED.value, turn.case_id, replace_draft_id),
                    )
                    existing_turns = [
                        item
                        if item.turn_id != replace_draft_id
                        else replace(item, state=TurnState.REPLACED)
                        for item in existing_turns
                    ]
                validate_parent_graph([*existing_turns, turn])
                self._insert_turn(connection, turn)
                connection.execute(
                    "UPDATE cases SET status = ?, updated_at = ? WHERE case_id = ?",
                    (target_status.value, updated_at, turn.case_id),
                )
                connection.commit()
        except sqlite3.Error as error:
            raise StorageError(f"turn write failed: {error}") from error
        actual_turns = self.get_turns(turn.case_id)
        actual = next((item for item in actual_turns if item.turn_id == turn.turn_id), None)
        actual_case = self.get_case(turn.case_id)
        if (
            actual != turn
            or actual_case.status is not target_status
            or actual_case.updated_at != updated_at
        ):
            raise StorageError("turn write read-back mismatch")
        if replace_draft_id is not None:
            replaced = next(
                (item for item in actual_turns if item.turn_id == replace_draft_id), None
            )
            if replaced is None or replaced.state is not TurnState.REPLACED:
                raise StorageError("Draft replacement read-back mismatch")
        return {
            "case_id": turn.case_id,
            "turn_id": turn.turn_id,
            "status": actual_case.status.value,
            "readback": "verified",
        }

    def close_case(
        self, updated: CaseRecord, *, reason: str, approved: bool
    ) -> Mapping[str, object]:
        """Atomically write only closure fields and verify the committed Case."""
        _require_approval(approved)
        validate_case(updated)
        try:
            with self._connect(writable=True) as connection:
                connection.execute("BEGIN IMMEDIATE")
                current = self._get_case(connection, updated.case_id)
                validate_transition(LifecycleTransition(current.status, updated.status, reason))
                connection.execute(
                    """UPDATE cases SET
                        updated_at = :updated_at,
                        status = :status,
                        outcome_score = :outcome_score,
                        outcome_class = :outcome_class,
                        outcome_notes = :outcome_notes,
                        user_rating = :user_rating,
                        what_worked = :what_worked,
                        what_failed = :what_failed,
                        next_test = :next_test,
                        closed_at = :closed_at
                    WHERE case_id = :case_id""",
                    _case_values(updated),
                )
                connection.commit()
        except sqlite3.Error as error:
            raise StorageError(f"case close failed: {error}") from error
        actual = self.get_case(updated.case_id)
        expected = to_jsonable(updated)
        observed = to_jsonable(actual)
        if not isinstance(expected, Mapping) or not isinstance(observed, Mapping):
            raise StorageError("case close read-back serialization failed")
        verification = verify_readback(expected, observed)
        if not verification.succeeded:
            raise StorageError("case close read-back mismatch")
        return {
            "case_id": actual.case_id,
            "status": actual.status.value,
            "readback": "verified",
        }
