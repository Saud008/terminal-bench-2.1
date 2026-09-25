# Rollout atlas schema contract

Publish writes a JSON object with:

- `schema_version` (integer, always `1`)
- `run_id` (string)
- `scenario` (string)
- `fleet` (string)
- `eligible` (array; copied verbatim from the ledger's `eligible` array, same order)
- `ineligible` (array; copied verbatim from the ledger's `ineligible` array, same order)
- `eligible_count` (integer)
- `ineligible_count` (integer)
- `audit_digest` (64-character lowercase hex SHA-256)

Publish must read eligibility from `/app/state/reconnect-ledger.json` and must not re-evaluate any gate or re-parse the scanned fleet inventory.

## audit_digest

For every device in the ledger — both `eligible` and `ineligible` rows — build one line:

```
{adapter_id}|{mac}|{eligible}|{reason}|{rank}
```

Where `{eligible}` is the literal string `true` for eligible rows or `false` for ineligible rows; `{reason}` is the empty string for eligible rows or the device's block reason for ineligible rows; `{rank}` is the device's decimal rank for eligible rows or the empty string for ineligible rows.

Collect one line per device from both arrays, **sort the lines lexicographically ascending as plain strings**, and join them with a single `\n` (no trailing newline). `audit_digest` is the SHA-256 hex digest of that exact UTF-8 encoded string.

Sorting the lines before hashing is required so that `audit_digest` does not depend on the order devices happen to appear in the fleet inventory or the ledger.
