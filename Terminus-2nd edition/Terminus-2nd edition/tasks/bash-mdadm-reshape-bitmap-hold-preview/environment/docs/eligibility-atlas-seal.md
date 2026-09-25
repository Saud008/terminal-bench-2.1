# Atlas schema contract

Publish writes a JSON object with:

- `schema_version` (integer, always `1`)
- `run_id` (string)
- `scenario` (string)
- `fleet` (string)
- `eligible` (array; copied verbatim from the ledger's `eligible` array, same order)
- `blocked` (array; copied verbatim from the ledger's `blocked` array, same order)
- `eligible_count` (integer)
- `blocked_count` (integer)
- `audit_digest` (64-character lowercase hex SHA-256)

Publish must read eligibility from `/app/state/reshape-ledger.json` and must not re-evaluate gates or re-parse the scanned inventory.

## audit_digest

Build the digest payload as this pipe-delimited UTF-8 string:

```
mdreshape|v1|{run_id}|{scenario}|{eligible_count}|{blocked_count}|{eligible_names}|{blocked_pairs}
```

Where `{eligible_names}` is the eligible array names joined with `,` in ledger order (empty string when there are none), and `{blocked_pairs}` is `name:block_reason` for each blocked array joined with `,` in ledger order (empty string when there are none).

`audit_digest` is the SHA-256 hex digest of that exact string, encoded as UTF-8. No trailing newline is added.
