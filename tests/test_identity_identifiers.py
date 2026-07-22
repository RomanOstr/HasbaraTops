import pytest

from dialogue_lab.case_identity import find_case, find_case_candidates
from dialogue_lab.errors import IdentifierError
from dialogue_lab.identifiers import next_case_id, next_turn_id
from tests.helpers import make_case


def test_case_id_is_definitive_and_root_lookup_returns_candidates() -> None:
    first = make_case(case_id="Case-001")
    second = make_case(case_id="Case-002")
    assert find_case("Case-002", [first, second]) == second
    assert find_case_candidates("123", "456", [first, second]) == [first, second]


def test_case_ids_use_a_global_unbounded_sequence() -> None:
    assert next_case_id([]) == "Case-001"
    assert next_case_id(["Case-001", "Case-009"]) == "Case-010"
    assert next_case_id(["Case-999"]) == "Case-1000"


def test_malformed_and_duplicate_case_ids_are_rejected() -> None:
    with pytest.raises(IdentifierError, match="malformed"):
        next_case_id(["CASE-17-1"])
    with pytest.raises(IdentifierError, match="malformed"):
        next_case_id(["Case-000"])
    with pytest.raises(IdentifierError, match="malformed"):
        next_case_id(["Case-0001"])
    with pytest.raises(IdentifierError, match="duplicate"):
        next_case_id(["Case-001", "Case-001"])


def test_turn_ids_are_case_local_and_sequential() -> None:
    assert next_turn_id([]) == "T001"
    assert next_turn_id(["T001", "T003"]) == "T004"
    assert next_turn_id(["T001"]) == "T002"


def test_malformed_and_duplicate_turn_ids_are_rejected() -> None:
    with pytest.raises(IdentifierError, match="malformed"):
        next_turn_id(["T1"])
    with pytest.raises(IdentifierError, match="duplicate"):
        next_turn_id(["T001", "T001"])
