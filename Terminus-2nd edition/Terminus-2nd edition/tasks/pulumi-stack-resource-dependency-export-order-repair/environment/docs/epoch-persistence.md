# Ledger epoch and adjacency digest

`/app/state/dep-ledger.json` is rewritten on every successful `order` run. Besides `stack`, `resources`, and `adjacency`, the ledger records run metadata used by export audits.

## Fields

| Field | Meaning |
|-------|---------|
| `epoch` | Monotonic counter starting at **1** on a fresh `/app/state` tree. Each successful `order` increments the previous epoch by one when `/app/state/dep-ledger.json` already exists. |
| `adjacency_digest` | Lowercase hex SHA-256 of the canonical adjacency JSON object: keys sorted lexicographically, each value list sorted lexicographically, UTF-8 JSON with no spaces after separators. |

## Cross-run behavior

`reset-state.sh` clears `/app/state` and `/app/output`. Within a verifier case that does **not** reset between two CLI invocations, the second successful `order` must persist `epoch` equal to the prior epoch plus one while recomputing `adjacency_digest` for the new adjacency map.

Export serialization reads the ledger file written in the same run. It must not recompute adjacency from the snapshot.
