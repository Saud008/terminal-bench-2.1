# Fixture catalog

Public maildir under `/app/fixtures/maildir/` is built at image time from `/app/fixtures/sources/*.eml` via `scripts/install-fixtures.sh`.

| Scenario | Notes |
|----------|-------|
| cur root-a :2,F | older duplicate of root-a |
| new root-a :2, | newer winner with X-Keywords stale |
| cur reply-a :2,SR | thread A reply, X-Keywords finance,urgent |
| cur root-b :2,S | separate thread B |
| new malformed | skipped (no Message-ID) |

Hidden maildir trees live under `/opt/verifier-fixtures/maildir/` (use `TB3_MAILDIR`). Each catalog row is checked against an independent reference implementation of the contracts in this folder.

Do not modify fixture contents during repair.
