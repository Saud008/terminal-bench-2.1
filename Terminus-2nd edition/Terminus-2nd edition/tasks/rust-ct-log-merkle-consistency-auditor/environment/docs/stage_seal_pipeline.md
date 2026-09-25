# Staging and seal pipeline

## Release binary

Rebuild with /app/environment/scripts/rebuild_ctwrelease.sh before running subcommands. The release binary path is documented in this file.

## Ingest

ctwrelease stage --audit-index FILE --witness-ledger FILE --staging OUT

FILE index lists bundle_file entries relative to the fixtures directory. Witness ledger lists checkpoints array. OUT must be /app/state/checkpoint_rows.json unless a different staging path is passed explicitly.

## Export

ctwrelease seal --staging IN --out OUT

Reads staging rows from /app/state/checkpoint_rows.json when IN points there. OUT must be /app/output/witness_evidence_archive.json for the compliance archive contract in /app/docs/sealed_evidence_archive.md.

## Overrides

TB3_AUDIT_INDEX replaces bundled audit index path.
TB3_WITNESS_LEDGER replaces bundled witness ledger path.
