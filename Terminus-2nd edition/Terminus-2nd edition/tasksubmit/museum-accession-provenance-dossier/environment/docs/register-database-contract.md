# Accession database schema

On this games museum accession playtest, /app/work/register.db table dossier_active is keyed by seed. Each active row binds archive, focus_accession_id, payload_json, archive_seq, and snapshot_digest. snapshot_digest is the lowercase SHA-256 hex digest of the exact bytes in /app/state/accession-vault.json when compose align reads it.

Later align for the same seed replaces the prior row even when archive changes.

Publish is permitted only when seed, archive, archive_seq, and snapshot_digest all
match the current vault snapshot and active row. Loading the same archive again
advances archive_seq and makes the previous aligned row stale; changing snapshot
bytes without advancing archive_seq also makes the row stale. Publish must reject
either case until compose align runs again. This freshness barrier prevents a
same-name reload or post-align snapshot mutation from publishing an older computed
payload.
