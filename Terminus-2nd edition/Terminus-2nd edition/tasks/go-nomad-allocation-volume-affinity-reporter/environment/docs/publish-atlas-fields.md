# Publish atlas fields

nomrep publish writes allocation affinity atlas JSON with seed, scenario, focus_alloc_id, run_id from the atlas index, volume_joins, placements, summary, and audit_digest.

Summary mirrors atlas_summary fields from the active compiled row, including drain_excluded and spread_penalty_total.

audit_digest is sha256 hex over a canonical JSON body with active_alloc_count, affinity_monotone_ok, constraint_pass_ok, drain_excluded, placement_ranks array, reschedule_total, spread_penalty_total, stale_suppressed, and sorted volume_keys from volume_joins.

Report files use caller-provided paths under /app/output/. Default nomrep publish examples use filenames ending in -placement-atlas.json such as seed-node-class-precedence-placement-atlas.json and seed-stale-allocation-filter-placement-atlas.json.
