"""Targeted canonical-write read-back comparison."""

from collections.abc import Mapping

from .models import WriteVerification


def verify_readback(
    expected: Mapping[str, object], actual: Mapping[str, object]
) -> WriteVerification:
    """Compare every expected field exactly."""
    mismatches: list[str] = []
    for key, expected_value in expected.items():
        if key not in actual:
            mismatches.append(f"missing field: {key}")
        elif actual[key] != expected_value:
            mismatches.append(f"value mismatch: {key}")
    return WriteVerification(
        succeeded=not mismatches,
        expected=dict(expected),
        actual=dict(actual),
        mismatches=tuple(mismatches),
    )
