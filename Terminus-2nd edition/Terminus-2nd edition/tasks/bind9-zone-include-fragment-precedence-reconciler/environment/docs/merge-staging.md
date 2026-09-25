# Merge staging artifact

After ingest writes a snapshot JSON file, write a sibling merge-staging.json file.

## Path

For snapshot /app/state/foo.json the staging path is /app/state/foo.json.merge-staging.json.

## Fields

staging_version is 1. snapshot_digest must equal canonical_snapshot_digest of the snapshot per digest-contract.md, not legacy effective key lists.

processing_order copies the snapshot list. record_count is the merged record count.

## Validation

export and verify may call validate_merge_staging; mismatch exits 4.
