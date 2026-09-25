# Staging ledger schema

Staging path: `/app/state/lease_audit_buffer.jsonl`

Rollup path: `/app/output/token_risk_rollup.json`

## Staged row

One compact JSON object per line, newline terminated.

| Field | Notes |
|-------|-------|
| event_id, token_id, parent_id, renewal_seq, mount, role, issued_at | Copied from the renewal event |
| policy_cap_sec | From policy revision resolution |
| static_cap_sec | Static TTL cap |
| lifetime_ceiling_sec, budget_remaining_sec | Lifetime budget |
| delegated_parent, granted_ttl_sec, admission | Delegation clamp |
| lineage_root, lineage_depth, is_orphan | Lineage graph |
| effective_renewable | Renewable inheritance |

An empty transcript directory yields an empty staging file (not an error). Re-running audit or rollup over unchanged inputs must rewrite byte-identical artifacts.

## Ordering

Ledger rows are ordered by depth key (cycle rows last), then `renewal_seq`, `token_id`, `event_id`.

## Verifier override

When `TB3_TRANSCRIPT_DIR` is set, audit reads `.lease-renew.jsonl` files from that path. Verifier-only transcripts live under `/opt/verifier-fixtures/vaultaud_renewal_hidden/`.
