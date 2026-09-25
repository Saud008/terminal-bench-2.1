# Staging schema

After successful ingest, `/app/state/` contains:

## staging-meta.json

| Field | Type | Meaning |
|-------|------|---------|
| pair_id | string | From pair manifest |
| pair_fingerprint | string | sha256(manifest + iptables + nft file bytes) |
| staging_digest | string | sha256 per pipeline-overview |
| iptables_sha256 | string | Hash of iptables source file |
| nft_sha256 | string | Hash of nft source file |
| tuple_counts | object | `iptables` and `nft` integer counts |
| policy_precedence | array | Ordered policy rows (see policy-precedence.md) |
| unsupported_features | array | Strings naming iptables `-m` modules with no nft mapping |

## NDJSON tuple lines

Each line in `iptables-tuples.ndjson` and `nft-tuples.ndjson`:

| Field | Type | Meaning |
|-------|------|---------|
| chain | string | Uppercase iptables chain or lowercase nft base chain name |
| ordinal | int | 1-based order within chain |
| policy | string or null | Chain default policy for policy rows only |
| match_key | string | Canonical normalized match fingerprint |
| target | string | ACCEPT, DROP, REJECT, or nft verdict |
| counter_packets | int | Packet counter |
| counter_bytes | int | Byte counter |
| hook_priority | int | nft hook priority rank (see policy-precedence.md) |

Policy rows use `ordinal` 0, non-null `policy`, empty `match_key`, and zero counters unless the save file includes bracket counters on the chain declaration line.

Tuple files are sorted by chain name ascending, then ordinal ascending.
