# Audit idempotency

SQLite database: /app/state/audit.db

## ingest action

First ingest of a bundle inserts one audit row with action ingest.

## revalidate

cbor-audit ingest --bundle <path> --revalidate on an unchanged bundle must not increase audit_row_count for that bundle_id. Revalidation updates metadata in place or no-ops when bundle_id and nonce match an existing ingest row.

Duplicate ingest rows break export attestation (audit_row_count must reflect unique ingests).

## Export coupling

export reads the latest snapshot from audit and reports audit_row_count for the bundle_id in the attestation JSON.
