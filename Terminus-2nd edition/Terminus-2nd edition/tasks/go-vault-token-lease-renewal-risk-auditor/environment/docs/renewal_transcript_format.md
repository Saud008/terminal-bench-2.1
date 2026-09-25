# Renewal transcript format

Each transcript file uses extension `.lease-renew.jsonl`. One JSON object per line.

## Event record

| Field | Type | Notes |
|-------|------|-------|
| event_id | string | Stable event identifier |
| token_id | string | Token identifier |
| parent_id | string | Parent token id; empty for root issuances |
| renewal_seq | int | Renewal counter for that `token_id`; unique per `token_id` |
| mount | string | Auth mount name; key into `mounts.json` |
| role | string | Role name; key into `roles.json` |
| policy_names | array | Policy names attached to the token |
| lease_ttl_sec | int | Requested lease TTL in seconds |
| renewable | bool | Caller-recorded renewable flag |
| orphan | bool | Issued detached from parent when true |
| issued_at | string | RFC3339 UTC issuance timestamp for this renewal |

## Corpus notes

Transcript files are read in lexicographic filename order; lines keep file order within each file.

| Term | Meaning |
|------|---------|
| origin renewal | Event of that `token_id` with the lowest `renewal_seq` |
| latest renewal | Event of that `token_id` with the highest `renewal_seq` |

Both views span the whole corpus, not a single file.

## Fatal ingest conditions

- mount absent from `mounts.json`
- role absent from `roles.json`
- empty `policy_names` list
