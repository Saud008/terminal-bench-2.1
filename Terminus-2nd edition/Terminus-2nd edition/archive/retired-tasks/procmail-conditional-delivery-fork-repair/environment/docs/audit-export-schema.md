# Audit export schema

The audit command reads `/app/state/delivery-snapshot.json` only and writes JSON to the output path.

Required top-level fields:

- `audit_version` (integer, always 1)
- `suite_id` (string)
- `environment` (object with HOST, HOSTNAME, ORGMAIL)
- `stats` (object, copied from snapshot stats)
- `deliveries` (array, copied from snapshot deliveries)
- `skipped_recipes` (array, copied entirely from snapshot skipped_recipes)
- `snapshot_sha256` (string, hex digest of the snapshot file bytes)

Audit must not drop skipped recipes. Each skipped entry has `recipe_id` and `reason`.
