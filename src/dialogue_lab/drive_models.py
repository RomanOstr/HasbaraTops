"""Typed envelopes for the runtime-managed Google Drive connector boundary."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorRequest:
    action: str
    file_id: str
    sheet: str | None
    payload: Mapping[str, object]
    source_revision_state: Mapping[str, str]


@dataclass(frozen=True)
class ConnectorResponse:
    connector_reported_success: bool
    record_identity: str | None
    values: Mapping[str, object]
    revision_state: Mapping[str, str]
    error_category: str | None = None
