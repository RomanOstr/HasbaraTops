from hasbaratops.facebook_url import parse_facebook_url
from hasbaratops.models import to_jsonable


def test_numeric_reel_and_comment_parse_with_exact_url_preserved() -> None:
    url = "https://www.facebook.com/reel/1810441076607036/?comment_id=1671769053915958&__tn__=R#x"
    parsed = parse_facebook_url(url)
    assert parsed.original_url == url
    assert parsed.post_id == "1810441076607036"
    assert parsed.root_comment_id == "1671769053915958"


def test_pfbid_post_and_reply_ids_parse() -> None:
    url = (
        "https://m.facebook.com/page/posts/pfbid012345?comment_id=10"
        "&reply_comment_id=11&__cft__%5B0%5D=tracking"
    )
    parsed = parse_facebook_url(url)
    assert parsed.normalized_host == "facebook.com"
    assert parsed.post_id == "pfbid012345"
    assert parsed.root_comment_id == "10"
    assert parsed.reply_comment_id == "11"


def test_photo_fbid_parses_as_post_id() -> None:
    parsed = parse_facebook_url("https://facebook.com/photo/?fbid=999&set=a.1")
    assert parsed.post_id == "999"


def test_reply_comment_id_does_not_create_parent_information() -> None:
    parsed = parse_facebook_url(
        "https://facebook.com/example/posts/123?comment_id=456&reply_comment_id=789"
    )
    serialized = to_jsonable(parsed)
    assert serialized["reply_comment_id"] == "789"
    assert "parent_turn_id" not in serialized


def test_repeated_conflicting_query_values_are_structured_errors() -> None:
    parsed = parse_facebook_url(
        "https://facebook.com/example/posts/123?comment_id=1&comment_id=2"
    )
    assert "conflicting_comment_id_values" in parsed.errors
    assert parsed.root_comment_id == "1"


def test_url_without_comment_is_valid_facebook_post() -> None:
    parsed = parse_facebook_url("https://www.facebook.com/example/posts/123")
    assert parsed.is_facebook_url
    assert parsed.post_id == "123"
    assert parsed.root_comment_id is None


def test_malformed_url_returns_structured_error() -> None:
    parsed = parse_facebook_url("facebook.com/reel/123")
    assert not parsed.is_facebook_url
    assert parsed.errors == ("malformed_url",)


def test_non_facebook_url_never_produces_facebook_ids() -> None:
    parsed = parse_facebook_url("https://example.com/posts/123?comment_id=456")
    assert not parsed.is_facebook_url
    assert parsed.post_id is None
    assert parsed.root_comment_id is None
