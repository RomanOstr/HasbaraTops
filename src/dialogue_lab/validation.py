"""Record-level deterministic validation."""

import re

from .enums import TurnDirection, TurnState
from .errors import DialogueLabError
from .facebook_url import parse_facebook_url
from .identifiers import TURN_ID_RE, case_id_number
from .lifecycle import CLOSED_STATUSES
from .models import CaseRecord, TurnRecord

PARTICIPANT_RE = re.compile(r"^(?:USER|P[1-9]\d*)$")


def validate_case(record: CaseRecord) -> None:
    case_id_number(record.case_id)
    required = {
        "case_title": record.case_title,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "topic": record.topic,
        "post_text": record.post_text,
        "post_url": record.post_url,
        "post_id": record.post_id,
        "root_comment_id": record.root_comment_id,
    }
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        raise DialogueLabError(f"missing required Case fields: {', '.join(missing)}")
    if not record.privacy_checked:
        raise DialogueLabError("Privacy Checked must be true")
    if record.outcome_score is not None and not 0 <= record.outcome_score <= 5:
        raise DialogueLabError("Outcome Score 0-5 must be between 0 and 5")
    if record.user_rating is not None and not 1 <= record.user_rating <= 5:
        raise DialogueLabError("User Rating 1-5 must be between 1 and 5")
    if record.status in CLOSED_STATUSES and not record.closed_at:
        raise DialogueLabError("Closed At is required for closed cases")

    parsed = parse_facebook_url(record.post_url)
    if not parsed.is_facebook_url:
        raise DialogueLabError("Post URL must be a Facebook URL")
    if parsed.post_id is not None and parsed.post_id != record.post_id:
        raise DialogueLabError("Post URL Post ID conflicts with Case Post ID")
    if parsed.root_comment_id is not None and parsed.root_comment_id != record.root_comment_id:
        raise DialogueLabError("Post URL Root Comment ID conflicts with Case Root Comment ID")
    if (
        record.status not in CLOSED_STATUSES
        and parsed.root_comment_id is None
        and parsed.reply_comment_id is None
    ):
        raise DialogueLabError("open Case Post URL requires a comment or reply identifier")


def validate_turn(record: TurnRecord) -> None:
    case_id_number(record.case_id)
    if TURN_ID_RE.fullmatch(record.turn_id) is None:
        raise DialogueLabError(f"malformed Turn ID: {record.turn_id}")
    if not PARTICIPANT_RE.fullmatch(record.participant_ref):
        raise DialogueLabError("Participant Ref must be USER or a case-local P-number")
    if not record.exact_text:
        raise DialogueLabError("Exact Text is required")
    if record.reply_comment_id is not None and not record.reply_comment_id.strip():
        raise DialogueLabError("reply_comment_id must not be blank")
    if not record.observed_at:
        raise DialogueLabError("Observed At is required")
    if record.direction is TurnDirection.INCOMING and record.state is TurnState.DRAFT:
        raise DialogueLabError("Incoming turns cannot be Draft")
    if record.exact_url is not None:
        parsed = parse_facebook_url(record.exact_url)
        if not parsed.is_facebook_url:
            raise DialogueLabError("Exact URL must be a Facebook URL")
        if parsed.post_id is not None and parsed.post_id != record.post_id:
            raise DialogueLabError("Exact URL Post ID conflicts with Turn Post ID")
        if parsed.root_comment_id is not None and parsed.root_comment_id != record.root_comment_id:
            raise DialogueLabError("Exact URL Root Comment ID conflicts with Turn Root Comment ID")
        if (
            parsed.reply_comment_id is not None
            and parsed.reply_comment_id != record.reply_comment_id
        ):
            raise DialogueLabError(
                "reply_comment_id must match the supplied Exact URL reply_comment_id"
            )
