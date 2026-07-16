"""Guard one operation against stale or mixed canonical-source state."""

from collections.abc import Iterable, Mapping

from .models import SourceConsistencyResult


def check_source_consistency(
    operation_start: Mapping[str, str],
    current: Mapping[str, str],
    *,
    material_sources: Iterable[str] | None = None,
) -> SourceConsistencyResult:
    """Compare revision states and block when a relevant source changed or vanished."""
    material = set(material_sources) if material_sources is not None else set(operation_start)
    changed: list[str] = []
    reasons: list[str] = []
    for source, start_state in operation_start.items():
        current_state = current.get(source)
        if current_state is None:
            changed.append(source)
            if source in material:
                reasons.append(f"{source} revision state is unavailable")
        elif current_state != start_state:
            changed.append(source)
            if source in material:
                reasons.append(f"{source} changed during the operation")
    for source in current.keys() - operation_start.keys():
        changed.append(source)
        if source in material:
            reasons.append(f"{source} was introduced during the operation")
    changed_tuple = tuple(sorted(set(changed)))
    requires_reload = any(source in material for source in changed_tuple)
    return SourceConsistencyResult(
        consistent=not reasons,
        operation_start=dict(operation_start),
        current=dict(current),
        changed_sources=changed_tuple,
        requires_reload=requires_reload,
        blocking_reasons=tuple(reasons),
    )
