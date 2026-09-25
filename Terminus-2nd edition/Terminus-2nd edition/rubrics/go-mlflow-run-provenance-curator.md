# Platform rubric — go-mlflow-run-provenance-curator

**Task folder:** tasks/go-mlflow-run-provenance-curator/

Agent builds mlprov from /app sources with go build readonly mod, +2
Agent ingest writes feature-ready staging snapshot with monotonic ingest_seq, +3
Agent scopes focus_run_id and parent links with seed-scoped FNV suffix, +3
Agent curate bind persists latest active row per seed in provenance.db, +3
Agent export reads staged snapshot plus active curated row together, +3
Agent computes root-first training run lineage_chain closure, +3
Agent normalizes model artifact rel_path before digest hashing, +2
Agent orders metric_epochs by epoch step then key ascending, +3
Agent sets epoch_monotonic_ok from ordered eval metric groups, +2
Agent validates feature dataset pins against manifest version_hash, +3
Agent applies TB3_MANIFEST_SALT suffix before binding comparison, +2
Agent computes audit_digest over fixed-key canonical summary body, +3
Agent export writes caller path under /app/output ending -provenance.json, +2
Agent ignores internal decoy package on ingest curate export hot path, +2
Agent re-ingest advances ingest_seq for same seed refresh detection, +2
Agent exports from staging alone without SQLite curated handoff, -3
Agent lineage_chain child-first or includes sibling runs, -3
Agent leaves leading ./ on artifact rel_path in export, -2
Agent metric_epochs out of epoch step key order, -2
Agent binding_ok true when pinned manifest hash mismatches, -3
Agent audit_digest uses alphabetically sorted object keys, -2
Agent curate bind keeps stale active row when scenario changes, -2
