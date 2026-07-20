from datetime import date

import pytest

from dialogue_lab.case_identity import find_duplicate_case, make_case_identity
from dialogue_lab.errors import DialogueLabError, IdentifierError
from dialogue_lab.identifiers import next_case_id, next_turn_id
from tests.helpers import make_case


def test_same_post_and_root_produce_same_identity() -> None:
    assert make_case_identity("post", "root") == make_case_identity("post", "root")


def test_different_roots_under_same_post_produce_different_identities() -> None:
    assert make_case_identity("post", "root-1") != make_case_identity("post", "root-2")


def test_missing_identity_component_is_rejected() -> None:
    with pytest.raises(DialogueLabError):
        make_case_identity("post", "  ")


def test_duplicate_case_lookup_reuses_existing_case() -> None:
    case = make_case()
    assert find_duplicate_case(case.identity, [case]) == case


def test_duplicate_canonical_rows_are_rejected() -> None:
    first = make_case(case_id="CASE-20260717-001")
    second = make_case(case_id="CASE-20260717-002")
    with pytest.raises(IdentifierError, match="duplicate canonical identity"):
        find_duplicate_case(first.identity, [first, second])


def test_case_ids_use_requested_jerusalem_date_and_sequence() -> None:
    assert next_case_id([], on_date=date(2026, 7, 17)) == "CASE-20260717-001"
    assert next_case_id(
        ["CASE-20260717-001", "CASE-20260716-009"], on_date=date(2026, 7, 17)
    ) == "CASE-20260717-002"


def test_malformed_and_duplicate_case_ids_are_rejected() -> None:
    with pytest.raises(IdentifierError, match="malformed"):
        next_case_id(["CASE-17-1"], on_date=date(2026, 7, 17))
    with pytest.raises(IdentifierError, match="duplicate"):
        next_case_id(
            ["CASE-20260717-001", "CASE-20260717-001"], on_date=date(2026, 7, 17)
        )


def test_turn_ids_are_case_local_and_sequential() -> None:
    assert next_turn_id([]) == "T001"
    assert next_turn_id(["T001", "T003"]) == "T004"
    assert next_turn_id(["T001"]) == "T002"


def test_malformed_and_duplicate_turn_ids_are_rejected() -> None:
    with pytest.raises(IdentifierError, match="malformed"):
        next_turn_id(["T1"])
    with pytest.raises(IdentifierError, match="duplicate"):
        next_turn_id(["T001", "T001"])
