# Watch and export schema

## Watch request

POST /v1/watch body:

- namespace_filter — prefix filter; only matching namespaces are delivered
- after_revision — cursor position; events with revision greater than this value are candidates
- limit — maximum delivered events (default 50)

## Watch response

- events — array of {revision, namespace, op, object, relation, subject}
- next_cursor — cursor position after this batch; clients must persist this value
- filtered_skips — count of revision rows skipped by namespace_filter

Cursor semantics: next_cursor advances only for delivered events. Filtered-out revision rows must not move the client cursor.

## Export trigger

POST /v1/export builds /app/output/authz-report.json from the latest /app/state/revision-snapshot.json.

Export does not re-read raw SQLite tuples; it evaluates probe checks against snapshot revision using closure cache and caveat rules.
