"""Enum values copied exactly from the live Case Log Data Dictionary."""

from enum import StrEnum


class StringEnum(StrEnum):
    """A string enum whose serialized value is the canonical Sheet value."""


class CaseStatus(StringEnum):
    DRAFT = "Draft"
    POSTED = "Posted"
    ACTIVE_EXCHANGE = "Active Exchange"
    CLOSED_NO_RESPONSE = "Closed - No Response"
    CLOSED_DISENGAGED = "Closed - Disengaged"
    CLOSED_SUBSTANTIVE = "Closed - Substantive"
    CLOSED_CLAIM_NARROWED = "Closed - Claim Narrowed"
    CLOSED_CORRECTION = "Closed - Correction"
    CLOSED_ABANDONED = "Closed - Abandoned"
    PENDING_SYNC = "Pending Sync"


class TurnDirection(StringEnum):
    INCOMING = "Incoming"
    OUTGOING = "Outgoing"


class TurnKind(StringEnum):
    COMMENT = "Comment"
    REPLY = "Reply"
    REACTION = "Reaction"


class TurnState(StringEnum):
    RECEIVED = "Received"
    DRAFT = "Draft"
    ANSWERED = "Answered"
    POSTED = "Posted"
    REPLACED = "Replaced"
    IGNORED = "Ignored"


class ParentConfidence(StringEnum):
    USER_CONFIRMED = "User-confirmed"
    URL_DERIVED = "URL-derived"
    SCREENSHOT = "Screenshot"
    INFERRED = "Inferred"
    UNKNOWN = "Unknown"


class OutcomeClass(StringEnum):
    NO_RESPONSE = "No Response"
    INSULT_REPETITION = "Insult/Repetition"
    SUBSTANTIVE_ENGAGEMENT = "Substantive Engagement"
    SOURCE_EXCHANGE = "Source Exchange"
    CLAIM_NARROWED = "Claim Narrowed"
    UNCERTAINTY_ACKNOWLEDGED = "Uncertainty Acknowledged"
    EXPLICIT_CORRECTION = "Explicit Correction"
    MIXED = "Mixed"
    ABANDONED = "Abandoned"
