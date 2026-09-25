# Manifest checkpoint schema

dbtsent ingest writes a JSON manifest snapshot to /app/state/manifest-checkpoint.json.

The snapshot records the active seed and pack name, a monotonically increasing ingest_seq, RFC3339 generated_at and evaluated_at timestamps copied from the pack, and seed-scoped model, source, and exposure catalogs used by evaluate scan and export alerts.

Each bundled pack JSON under /app/fixtures/bundles/ includes pack_name matching the pack slug such as core-lineage.

Each model row carries unique_id, depends_on, enabled, and last_built_at. Each source row carries unique_id, loaded_at, warn_after_minutes, and error_after_minutes. Each exposure row carries unique_id and depends_on model references.

Seed-scoped unique_id transform (required on every model, source, exposure unique_id and every depends_on model reference written into the checkpoint):

  scoped = `{raw_unique_id}-{fnv1a32_hex8}`

where `fnv1a32` is the 32-bit FNV-1a hash of the UTF-8 bytes of `{seed}:{raw_unique_id}`:

  offset basis 2166136261, prime 16777619, result formatted as eight lowercase hex digits

Example shape: `model.analytics.stg_orders-71ceca88` (suffix depends on seed). Bare fixture unique_ids without the `-{hex8}` suffix are invalid in the checkpoint.

Before writing a new checkpoint, read any existing /app/state/manifest-checkpoint.json and set ingest_seq to previous ingest_seq + 1 (or 1 when no prior checkpoint exists). Re-ingesting the same seed and bundle without clearing state must bump ingest_seq by exactly one.

export alerts must reject seed or bundle values that do not match the on-disk checkpoint.
