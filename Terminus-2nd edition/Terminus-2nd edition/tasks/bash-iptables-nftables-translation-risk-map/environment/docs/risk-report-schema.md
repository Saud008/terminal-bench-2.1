# Risk report schema

Export writes JSON with these top-level fields:

| Field | Type | Required |
|-------|------|----------|
| schema_version | string | always `"1"` |
| pair_id | string | yes |
| staging_digest | string | yes |
| run_seq | int | from run-seq.json after export |
| summary | object | counts by severity: high, medium, low |
| findings | array | risk rows |
| unsupported | array | copied from staging-meta |
| counter_drift | array | counter mismatches |
| policy_precedence | array | copied from staging-meta |

## Finding object

| Field | Type | Meaning |
|-------|------|---------|
| category | string | one of: chain_policy_precedence, match_extension_normalization, rule_ordering, counter_preservation |
| severity | string | high, medium, or low |
| chain | string | affected chain |
| iptables_ordinal | int or null | |
| nft_ordinal | int or null | |
| detail | string | human-readable reason |

Severity rules:

- **high** — policy default mismatch between iptables chain and mapped nft base chain
- **medium** — rule ordering swap within a chain, or counter drift greater than zero on matched rules
- **low** — match normalization gap where targets agree but normalized match_key differs

Findings array is sorted by category, then chain, then iptables_ordinal.

## counter_drift rows

Each row: `chain`, `ordinal`, `iptables_packets`, `nft_packets`, `iptables_bytes`, `nft_bytes`.

Only include rows where a rule pair shares the same normalized match_key and target but counters differ.
