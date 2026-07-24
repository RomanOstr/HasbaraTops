"""Deterministic Facebook URL parsing with exact-input preservation."""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlsplit

from .models import ParsedFacebookURL


def _query_value(query: dict[str, list[str]], key: str, errors: list[str]) -> str | None:
    values = [value.strip() for value in query.get(key, []) if value.strip()]
    distinct = list(dict.fromkeys(values))
    if len(distinct) > 1:
        errors.append(f"conflicting_{key}_values")
    return distinct[0] if distinct else None


def parse_facebook_url(original_url: str) -> ParsedFacebookURL:
    """Parse supported Facebook identifiers without rewriting the supplied URL."""
    errors: list[str] = []
    try:
        parsed = urlsplit(original_url)
        host = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return ParsedFacebookURL(original_url, None, None, None, None, False, ("malformed_url",))

    if parsed.scheme.lower() not in {"http", "https"} or not host:
        return ParsedFacebookURL(original_url, None, None, None, None, False, ("malformed_url",))

    is_facebook = host == "facebook.com" or host.endswith(".facebook.com")
    if not is_facebook:
        return ParsedFacebookURL(
            original_url, host, None, None, None, False, ("non_facebook_url",)
        )

    query = parse_qs(parsed.query, keep_blank_values=True)
    root_comment_id = _query_value(query, "comment_id", errors)
    reply_comment_id = _query_value(query, "reply_comment_id", errors)
    segments = [unquote(segment) for segment in parsed.path.split("/") if segment]
    post_id: str | None = None

    for marker in ("reel", "posts"):
        if marker in segments:
            index = segments.index(marker)
            if index + 1 < len(segments) and segments[index + 1].strip():
                post_id = segments[index + 1].strip()
                break
    if post_id is None and segments and segments[-1] in {"photo.php", "photo"}:
        post_id = _query_value(query, "fbid", errors)
    if post_id is None and "fbid" in query:
        post_id = _query_value(query, "fbid", errors)
    if post_id is None:
        errors.append("post_id_not_found")

    return ParsedFacebookURL(
        original_url=original_url,
        normalized_host="facebook.com",
        post_id=post_id,
        root_comment_id=root_comment_id,
        reply_comment_id=reply_comment_id,
        is_facebook_url=True,
        errors=tuple(errors),
    )
