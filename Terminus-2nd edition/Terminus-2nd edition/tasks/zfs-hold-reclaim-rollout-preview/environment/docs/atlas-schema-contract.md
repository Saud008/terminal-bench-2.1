# Atlas schema contract

Publish writes a JSON object that includes every ledger field plus:

- `audit_digest` (64-character lowercase hex SHA-256)
- `focus_snapshots` (array; echo inventory `focus_snapshots` or `[]` when absent)

## audit_digest

Let `names` be the eligible snapshot names ordered by ascending `reclaim_rank`.

Build the UTF-8 payload as each name followed by a newline, including a trailing newline after the last name. If there are zero eligible snapshots, the payload is empty (zero bytes).

`audit_digest` is the SHA-256 hex digest of that payload.

Publish must read eligibility from `/app/state/reclaim-ledger.json` and must not re-evaluate gates.
