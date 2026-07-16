import pytest

from dialogue_lab.enums import (
    CaseStatus,
    ParentConfidence,
    TurnDirection,
    TurnKind,
    TurnState,
)
from dialogue_lab.errors import DialogueLabError, GraphError, LifecycleError
from dialogue_lab.lifecycle import (
    validate_closure_evidence,
    validate_draft_creation,
    validate_posted_turn,
    validate_transition,
)
from dialogue_lab.models import LifecycleTransition, to_jsonable
from dialogue_lab.parent_graph import is_branched, thread_map, validate_parent_graph
from dialogue_lab.validation import validate_turn
from tests.helpers import make_reply, make_turn


def test_invalid_lifecycle_transition_fails() -> None:
    with pytest.raises(LifecycleError, match="invalid"):
        validate_transition(
            LifecycleTransition(CaseStatus.DRAFT, CaseStatus.CLOSED_CORRECTION, "not posted")
        )


def test_approved_reply_can_become_draft_but_exploratory_cannot() -> None:
    draft = make_reply(
        "T002",
        "T001",
        participant_ref="USER",
        direction=TurnDirection.OUTGOING,
        state=TurnState.DRAFT,
    )
    validate_draft_creation(draft, explicitly_approved=True, explicitly_saved=False)
    with pytest.raises(LifecycleError, match="exploratory"):
        validate_draft_creation(draft, explicitly_approved=False, explicitly_saved=False)


def test_exact_posted_wording_is_independent_of_recommendation() -> None:
    recommendation = "Suggested synthetic wording."
    posted = make_reply(
        "T002",
        "T001",
        participant_ref="USER",
        direction=TurnDirection.OUTGOING,
        state=TurnState.POSTED,
        exact_text="Edited wording actually posted.",
    )
    validate_posted_turn(posted)
    assert posted.exact_text != recommendation
    assert to_jsonable(posted)["exact_text"] == "Edited wording actually posted."


def test_parent_must_exist_in_same_case() -> None:
    with pytest.raises(GraphError, match="does not exist"):
        validate_parent_graph([make_turn(), make_reply("T002", "T999")])


def test_cycles_are_rejected() -> None:
    first = make_reply("T001", "T002")
    second = make_reply("T002", "T001")
    with pytest.raises(GraphError, match="cycle"):
        validate_parent_graph([first, second])


def test_multiple_children_and_parent_confidence_are_retained() -> None:
    root = make_turn()
    first = make_reply("T002", "T001", parent_confidence=ParentConfidence.SCREENSHOT)
    second = make_reply("T003", "T001", parent_confidence=ParentConfidence.UNKNOWN)
    validate_parent_graph([root, first, second])
    assert is_branched([root, first, second])
    mapped = thread_map([root, first, second])
    assert mapped[1].parent_turn_id == "T001"
    assert first.parent_confidence is ParentConfidence.SCREENSHOT


def test_reply_without_parent_is_rejected_even_with_reply_comment_id() -> None:
    reply_without_parent = make_turn(
        turn_id="T002",
        kind=TurnKind.REPLY,
        reply_comment_id="789",
        parent_turn_id=None,
        parent_confidence=None,
    )
    with pytest.raises(GraphError, match="requires Parent Turn ID"):
        validate_parent_graph([make_turn(), reply_without_parent])


def test_participant_names_and_profile_urls_are_rejected() -> None:
    with pytest.raises(DialogueLabError, match="Participant Ref"):
        validate_turn(make_turn(participant_ref="Synthetic Name"))
    with pytest.raises(DialogueLabError, match="Participant Ref"):
        validate_turn(make_turn(participant_ref="https://facebook.com/profile"))


@pytest.mark.parametrize("signal", ["silence", "reaction", "deletion", "blocking"])
def test_closure_cannot_infer_persuasion_from_non_probative_signal(signal: str) -> None:
    with pytest.raises(LifecycleError, match="cannot be inferred"):
        validate_closure_evidence(claimed_persuasion=True, evidence={signal})


def test_valid_turn_preserves_exact_quote_without_rewriting() -> None:
    exact = 'Synthetic quote: "Keep punctuation — exactly."'
    turn = make_turn(exact_text=exact)
    validate_turn(turn)
    assert turn.exact_text == exact
