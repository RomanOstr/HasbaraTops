# CLI payload contracts

All payloads are UTF-8 JSON. Field names are lowercase `snake_case`. Unknown fields and missing required values are rejected before mutation.

## Database import

`db-import` accepts one object:

```json
{
  "cases": [
    {
      "case_id": "Case-004",
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

Every imported Case and Turn requires its allocated identifier. Case IDs must use `Case-NNN` from the global sequence. `source_links` is an array. Open Cases require an exact Facebook comment or reply permalink.

## Case lookup

`case-find --case-id Case-004` uses `case_id` as the definitive key and returns exactly that Case when it exists. `case-find --post-id 123 --root-comment-id 456` returns a `candidates` list because multiple Cases may intentionally track separate reply branches under one Facebook root. A root match never silently selects or reuses a Case.

`case-list-open` reports `last_turn_id`, `last_comment_permalink`, and `permalink_status` for each open Case. The permalink is the latest public Turn's supplied exact URL. A missing URL is reported as null with `permalink_status: "missing"`; the Case root URL is never substituted. Latest-Turn ordering is a presentation choice, not Case or Turn identity.

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

The command allocates the next globally unique sequential Case ID and derives Case-local Turn IDs. It does not treat `post_id + root_comment_id` as Case identity, so another Case may be created for a separate branch under the same root.

Turn duplicate detection first uses a supplied permalink's non-null `reply_comment_id`, which is globally unique across Turns. Otherwise it uses the exact tuple `case_id + parent_turn_id + direction + exact_text`. A root Turn participates in the fallback with `parent_turn_id: null`. Mutable state, timestamps, ordering, and the latest reply do not determine identity.

## Follow-up and posting

`case-followup` and `case-record-posting` accept one Turn without `case_id`, `turn_id`, `post_id`, or `root_comment_id`. Required Turn fields match the intake example.

A posting payload must use `direction: "Outgoing"` and `state: "Posted"`. It may include `draft_turn_id` to mark one existing Outgoing Draft as Replaced in the same transaction.

## Branch split

```text
HasbaraTops case-split-branch --case-id <id> --branch-root-turn-id <turn-id> --new-case-title <title> --new-topic <topic> --backup-destination <outside-repo-path> --approved
```

The branch root must be a non-root Turn with another branch remaining in the source Case. The command allocates the next global Case ID, copies the shared ancestor path with fresh case-local Turn IDs, moves the selected branch and all descendants, preserves exact public text and URLs, and verifies the backup and both committed graphs. It stops when a copied shared ancestor has `reply_comment_id`, because that identifier is globally unique.

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

## Identity migration

```text
HasbaraTops db-migrate-identity --backup-destination <outside-repo-path> --approved
```

This command is the only supported path for renumbering an existing canonical database. It requires explicit approval, creates and verifies a non-overwriting backup, preserves schema version 1, renumbers Cases in stable creation/allocation order, updates every Turn and graph reference transactionally, and verifies the committed mapping and integrity before success. Its JSON receipt reports the backup, unchanged schema version, migrated counts, committed read-back, and integrity result. A failed migration rolls back and blocks further writes until rollback and integrity are verified.
