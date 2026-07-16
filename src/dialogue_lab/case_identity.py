"""Canonical case identity helpers."""

from collections.abc import Iterable

from .errors import IdentifierError
from .models import CaseIdentity, CaseRecord


def make_case_identity(post_id: str, root_comment_id: str) -> CaseIdentity:
    return CaseIdentity(post_id, root_comment_id)


def find_duplicate_case(
    identity: CaseIdentity, cases: Iterable[CaseRecord]
) -> CaseRecord | None:
    matches = [case for case in cases if case.identity == identity]
    if len(matches) > 1:
        ids = ", ".join(case.case_id for case in matches)
        raise IdentifierError(f"duplicate canonical identity already exists in cases: {ids}")
    return matches[0] if matches else None
