# Delegation clamp schema

## Staged fields

| Field | Type | Notes |
|-------|------|-------|
| delegated_parent | string | Parent token id when lineage resolves completely; empty for orphan, missing-ancestor, and cycle rows |
| granted_ttl_sec | int | Admitted lease length for this renewal; zero when denied |
| admission | string | `granted` when `granted_ttl_sec` > 0; otherwise `denied` |

Denied renewals remain in the staging ledger; they are not ingest errors.
