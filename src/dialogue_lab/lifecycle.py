"""Deterministic lifecycle and observable-outcome enforcement."""

from .enums import CaseStatus, TurnDirection, TurnState
from .errors import LifecycleError
from .models import LifecycleTransition, TurnRecord

CLOSED_STATUSES = {
    CaseStatus.CLOSED_NO_RESPONSE,
    CaseStatus.CLOSED_DISENGAGED,
    CaseStatus.CLOSED_SUBSTANTIVE,
    CaseStatus.CLOSED_CLAIM_NARROWED,
    CaseStatus.CLOSED_CORRECTION,
    CaseStatus.CLOSED_ABANDONED,
}

ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.DRAFT: {CaseStatus.POSTED, CaseStatus.PENDING_SYNC},
    CaseStatus.POSTED: {CaseStatus.ACTIVE_EXCHANGE, CaseStatus.PENDING_SYNC, *CLOSED_STATUSES},
    CaseStatus.ACTIVE_EXCHANGE: {CaseStatus.PENDING_SYNC, *CLOSED_STATUSES},
    CaseStatus.PENDING_SYNC: {
        CaseStatus.DRAFT,
        CaseStatus.POSTED,
        CaseStatus.ACTIVE_EXCHANGE,
        *CLOSED_STATUSES,
    },
    **{status: set() for status in CLOSED_STATUSES},
}


def validate_transition(transition: LifecycleTransition) -> None:
    if transition.from_status == transition.to_status:
        return
    if transition.to_status not in ALLOWED_TRANSITIONS[transition.from_status]:
        raise LifecycleError(
            f"invalid case transition: {transition.from_status.value} -> "
            f"{transition.to_status.value}"
        )
    if not transition.reason.strip():
        raise LifecycleError("lifecycle transition reason is required")


def validate_draft_creation(
    turn: TurnRecord, *, explicitly_approved: bool, explicitly_saved: bool
) -> None:
    if turn.direction is not TurnDirection.OUTGOING or turn.state is not TurnState.DRAFT:
        raise LifecycleError("a saved draft must be an Outgoing turn in Draft state")
    if not (explicitly_approved or explicitly_saved):
        raise LifecycleError("exploratory or unapproved drafts must not be logged")


def validate_posted_turn(turn: TurnRecord) -> None:
    if turn.direction is not TurnDirection.OUTGOING or turn.state is not TurnState.POSTED:
        raise LifecycleError("posting confirmation requires an Outgoing Posted turn")
    if not turn.exact_text:
        raise LifecycleError("exact published wording is required")


def validate_closure_evidence(*, claimed_persuasion: bool, evidence: set[str]) -> None:
    """Reject outcome inference from signals the Manual says are non-probative."""
    non_probative = {"silence", "deletion", "blocking", "reaction", "disappearance"}
    if claimed_persuasion and evidence and evidence <= non_probative:
        raise LifecycleError("persuasion cannot be inferred from the supplied closure signals")
