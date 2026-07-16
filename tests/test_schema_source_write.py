import copy

import pytest

from dialogue_lab.drive_protocol import CASE_LOG_ID, GENERAL_RESPONSES_ID, connector_request
from dialogue_lab.errors import CompatibilityError, WriteSafetyError
from dialogue_lab.manual_version import require_supported_manual
from dialogue_lab.models import DriveWriteRequest
from dialogue_lab.readback import verify_readback
from dialogue_lab.schema import expected_schema_payload, schema_signature, validate_schema
from dialogue_lab.source_consistency import check_source_consistency


def _observed_schema() -> dict[str, object]:
    expected = expected_schema_payload()
    headers = expected["headers"]
    assert isinstance(headers, dict)
    return {
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


def test_manual_version_27_is_supported() -> None:
    version, warnings = require_supported_manual("Version 2.7 — synthetic")
    assert str(version) == "2.7"
    assert warnings == ()


def test_manual_below_minimum_and_unknown_major_fail() -> None:
    with pytest.raises(CompatibilityError, match="older"):
        require_supported_manual("Version 2.6")
    with pytest.raises(CompatibilityError, match="major"):
        require_supported_manual("Version 3.0")


def test_newer_minor_warns_without_claiming_sync() -> None:
    version, warnings = require_supported_manual("Version 2.8")
    assert str(version) == "2.8"
    assert warnings and "revalidate" in warnings[0]


def test_live_shape_schema_signature_is_deterministic() -> None:
    first = validate_schema(_observed_schema())
    second = schema_signature()
    assert first == second
    assert len(first.value) == 64


def test_header_enum_and_formula_mismatch_block_writes() -> None:
    header_bad = _observed_schema()
    assert isinstance(header_bad["sheets"], dict)
    header_bad["sheets"]["Cases"] = ["Wrong"]
    with pytest.raises(CompatibilityError, match="header mismatch"):
        validate_schema(header_bad)

    enum_bad = _observed_schema()
    assert isinstance(enum_bad["enums"], dict)
    enum_bad["enums"]["Turns.State"] = ["Received"]
    with pytest.raises(CompatibilityError, match="enum mismatch"):
        validate_schema(enum_bad)

    formula_bad = _observed_schema()
    formula_bad["dashboard_formulas"] = []
    with pytest.raises(CompatibilityError, match="Dashboard formulas"):
        validate_schema(formula_bad)


def test_changed_manual_or_schema_requires_revalidation() -> None:
    start = {"manual": "r1", "case_log_schema": "s1", "strategy": "r1"}
    manual_changed = check_source_consistency(start, {**start, "manual": "r2"})
    assert not manual_changed.consistent and manual_changed.requires_reload
    schema_changed = check_source_consistency(start, {**start, "case_log_schema": "s2"})
    assert not schema_changed.consistent


def test_non_material_change_can_remain_consistent() -> None:
    start = {"manual": "r1", "strategy": "r1"}
    result = check_source_consistency(
        start, {"manual": "r1", "strategy": "r2"}, material_sources={"manual"}
    )
    assert result.consistent
    assert result.changed_sources == ("strategy",)


def test_readback_requires_exact_text_and_every_expected_field() -> None:
    expected = {"Turn ID": "T001", "Exact Text": "exact", "State": "Posted"}
    assert verify_readback(expected, copy.deepcopy(expected)).succeeded
    mismatch = verify_readback(expected, {"Turn ID": "T001", "Exact Text": "changed"})
    assert not mismatch.succeeded
    assert "value mismatch: Exact Text" in mismatch.mismatches
    assert "missing field: State" in mismatch.mismatches


def test_connector_success_without_matching_readback_is_still_failure() -> None:
    connector_response = {"success": True}
    result = verify_readback({"Case ID": "CASE-20260717-001"}, connector_response)
    assert not result.succeeded


def test_write_policy_rejects_unapproved_protected_and_arbitrary_targets() -> None:
    unapproved = DriveWriteRequest(
        operation="append_case",
        target_file_id=CASE_LOG_ID,
        target_sheet="Cases",
        record_identity="CASE-20260717-001",
        values={"Case ID": "CASE-20260717-001"},
        explicitly_approved=False,
    )
    with pytest.raises(WriteSafetyError, match="approval"):
        connector_request(unapproved, {"manual": "r1"})
    protected = DriveWriteRequest(
        operation="append_case",
        target_file_id=GENERAL_RESPONSES_ID,
        target_sheet="Cases",
        record_identity="CASE-20260717-001",
        values={"Case ID": "CASE-20260717-001"},
        explicitly_approved=True,
    )
    with pytest.raises(WriteSafetyError, match="protected"):
        connector_request(protected, {"manual": "r1"})


def test_valid_case_log_write_builds_typed_connector_envelope() -> None:
    request = DriveWriteRequest(
        operation="append_turn",
        target_file_id=CASE_LOG_ID,
        target_sheet="Turns",
        record_identity="CASE-20260717-001:T001",
        values={"Turn ID": "T001"},
        explicitly_approved=True,
    )
    envelope = connector_request(request, {"manual": "r1", "case_log": "m1"})
    assert envelope.action == "append_turn"
    assert envelope.source_revision_state["manual"] == "r1"
