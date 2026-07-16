"""Validation and presentation of case-local public-turn parent graphs."""

from collections import Counter
from collections.abc import Iterable

from .enums import TurnKind
from .errors import GraphError
from .models import ThreadMapEntry, TurnRecord


def validate_parent_graph(turns: Iterable[TurnRecord]) -> None:
    records = list(turns)
    ids = [turn.turn_id for turn in records]
    duplicates = [turn_id for turn_id, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise GraphError(f"duplicate Turn IDs: {', '.join(sorted(duplicates))}")
    by_id = {turn.turn_id: turn for turn in records}
    case_ids = {turn.case_id for turn in records}
    if len(case_ids) > 1:
        raise GraphError("parent graph must contain turns from exactly one case")

    for turn in records:
        if turn.parent_turn_id == turn.turn_id:
            raise GraphError(f"turn {turn.turn_id} cannot parent itself")
        if turn.parent_turn_id is not None:
            if turn.parent_turn_id not in by_id:
                raise GraphError(f"parent {turn.parent_turn_id} does not exist in the case")
            if turn.parent_confidence is None:
                raise GraphError(f"turn {turn.turn_id} requires Parent Confidence")
        elif turn.kind is TurnKind.REPLY:
            raise GraphError(f"reply {turn.turn_id} requires Parent Turn ID")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(turn_id: str) -> None:
        if turn_id in visiting:
            raise GraphError("parent graph contains a cycle")
        if turn_id in visited:
            return
        visiting.add(turn_id)
        parent = by_id[turn_id].parent_turn_id
        if parent is not None:
            visit(parent)
        visiting.remove(turn_id)
        visited.add(turn_id)

    for turn_id in by_id:
        visit(turn_id)


def is_branched(turns: Iterable[TurnRecord]) -> bool:
    parents = Counter(turn.parent_turn_id for turn in turns if turn.parent_turn_id is not None)
    return any(count > 1 for count in parents.values())


def thread_map(
    turns: Iterable[TurnRecord], *, excerpt_length: int = 80
) -> tuple[ThreadMapEntry, ...]:
    records = list(turns)
    validate_parent_graph(records)
    return tuple(
        ThreadMapEntry(
            turn_id=turn.turn_id,
            parent_turn_id=turn.parent_turn_id,
            participant_ref=turn.participant_ref,
            excerpt=turn.exact_text.replace("\n", " ")[:excerpt_length],
            state=turn.state,
        )
        for turn in records
    )
