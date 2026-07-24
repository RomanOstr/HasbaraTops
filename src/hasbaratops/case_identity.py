"""Definitive Case-ID lookup and secondary Facebook-root discovery."""

from collections.abc import Iterable

from .models import CaseRecord


def find_case(case_id: str, cases: Iterable[CaseRecord]) -> CaseRecord | None:
    """Resolve one Case by its definitive identifier."""
    return next((case for case in cases if case.case_id == case_id), None)


def find_case_candidates(
    post_id: str, root_comment_id: str, cases: Iterable[CaseRecord]
) -> list[CaseRecord]:
    """Return all Cases on a root; callers must select by definitive Case ID."""
    return [
        case
        for case in cases
        if case.post_id == post_id and case.root_comment_id == root_comment_id
    ]
