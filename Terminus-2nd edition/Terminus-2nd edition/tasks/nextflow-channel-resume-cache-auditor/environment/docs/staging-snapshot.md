# Staging snapshot

Path: /app/state/resume-stage.json

Written by ingest; audit increments audit_generation on the snapshot.

## Fields

- engine: nfresume-v1
- scenario, run_id, session_id, resumed from run.meta.json
- task_count: number of staged tasks
- tasks: array of staged task rows
- audit_generation: bumped by audit after findings persist
- run_digest: SHA-256 over run_id and task_ids in trace order

## Staged task row

Each tasks[] element includes:

- task_id, hash, parent_hashes
- lineage_digest: admitted claim — trace lineage_digest when present, otherwise SHA-256 chain of parent_hashes root-first then task hash (NUL separated)
- container_digest: normalized digest
- expansion_hash: recorded from trace
- computed_expansion_hash: recomputed from input_globs at ingest
- attempt, cached, exit_status
- prior_digest, prior_exit_status when present
- cache_session_id from work/.nf_cached.json when present

Tasks are ordered by trace filename sort order.
