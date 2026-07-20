# CLI payload contracts

All payloads are UTF-8 JSON. Field names are lowercase `snake_case`. Unknown fields and missing required values are rejected before mutation.

## Database import

`db-import` accepts one object:

```json
{
  "cases": [
    {
      "case_id": "CASE-20260720-001",
      "case_title": "Short title",
      "created_at": "2026-07-20 10:00",
      "updated_at": "2026-07-20 10:00",
      "status": "Posted",
      "topic": "Topic",
      "post_text": "Exact public post text",
      "post_url": "https://www.facebook.com/example/posts/123?comment_id=456",
      "post_id": "123",
      "root_comment_id": "456",
      "source_links": [],
      "privacy_checked": true,
      "outcome_score": null,
      "outcome_class": null,
      "outcome_notes": "",
      "user_rating": null,
      "what_worked": "",
      "what_failed": "",
      "next_test": "",
      "closed_at": ""
    }
  ],
  "turns": []
}
```

Every imported Case and Turn requires its allocated identifier. `source_links` is an array. Open Cases require an exact Facebook comment or reply permalink.

## Case intake

`case-intake` accepts a Case without `case_id` and zero or more Turns without `case_id` or `turn_id`:

```json
{
  "case": {
    "case_title": "Short title",
    "created_at": "2026-07-20 10:00",
    "updated_at": "2026-07-20 10:00",
    "status": "Posted",
    "topic": "Topic",
    "post_text": "Exact public post text",
    "post_url": "https://www.facebook.com/example/posts/123?comment_id=456",
    "post_id": "123",
    "root_comment_id": "456",
    "source_links": [],
    "privacy_checked": true
  },
  "turns": [
    {
      "parent_turn_id": null,
      "parent_confidence": null,
      "participant_ref": "P1",
      "direction": "Incoming",
      "kind": "Comment",
      "state": "Received",
      "exact_text": "Exact public comment",
      "reply_comment_id": null,
      "exact_url": "https://www.facebook.com/example/posts/123?comment_id=456",
      "url_supplied_at": "2026-07-20 10:00",
      "observed_at": "2026-07-20 10:00",
      "notes": ""
    }
  ]
}
```

The command derives Case and Turn identifiers and forces each Turn identity to match the Case.

## Follow-up and posting

`case-followup` and `case-record-posting` accept one Turn without `case_id`, `turn_id`, `post_id`, or `root_comment_id`. Required Turn fields match the intake example.

A posting payload must use `direction: "Outgoing"` and `state: "Posted"`. It may include `draft_turn_id` to mark one existing Outgoing Draft as Replaced in the same transaction.

## Closeout

`case-close` accepts:

```json
{
  "status": "Closed - Substantive",
  "updated_at": "2026-07-21 10:00",
  "outcome_score": 3,
  "outcome_class": "Substantive Engagement",
  "outcome_notes": "Observable outcome only",
  "user_rating": null,
  "what_worked": "Concise observation",
  "what_failed": "Concise observation",
  "next_test": "One controlled test",
  "closed_at": "2026-07-21 10:00",
  "reason": "explicit closeout"
}
```

Only closure fields are updated. The Case identity and public context remain unchanged.
