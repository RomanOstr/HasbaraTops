"""Targeted canonical-write read-back comparison."""

from collections.abc import Mapping

from .models import DriveWriteVerification


def verify_readback(
    expected: Mapping[str, object], actual: Mapping[str, object]
) -> DriveWriteVerification:
    """Compare every expected field exactly; connector success alone is irrelevant."""
    mismatches: list[str] = []
    for key, expected_value in expected.items():
        if key not in actual:
            mismatches.append(f"missing field: {key}")
        elif actual[key] != expected_value:
            mismatches.append(f"value mismatch: {key}")
    return DriveWriteVerification(
        succeeded=not mismatches,
        expected=dict(expected),
        actual=dict(actual),
        mismatches=tuple(mismatches),
    )
