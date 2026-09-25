# Atlas index schema

/app/var/atlas-index.db stores atlas_runs and atlas_summary. Pytest persistence checks may query these tables with sqlite3.

Each nomrep compile replaces all prior rows. The latest run for a seed and scenario wins even when the scenario name changes for that seed.

atlas_runs records seed, scenario, focus_alloc_id, and load_seq from the placement buffer.

atlas_summary stores active_alloc_count, stale_suppressed, drain_excluded, reschedule_total, volume_join_count, spread_penalty_total, constraint_pass_ok, affinity_monotone_ok, and placements_json.

Audit digests in published atlases use sha256 over canonical summary JSON per publish-atlas-fields.md. The hashlib module matches that contract in verifier math.
