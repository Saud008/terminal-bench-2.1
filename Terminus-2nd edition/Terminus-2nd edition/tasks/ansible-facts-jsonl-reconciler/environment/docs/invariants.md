# Post-reconcile invariants

After `facts-chain reconcile`, `stage`, and `export` on JSONL stream `J` with `--run-id R`:

1. Host identity in `hosts` and `fact_snapshots` uses `inventory_uuid`, never `hostname`.
2. For each `(inventory_uuid, fact_key)`, the stored value comes from the JSONL row with the greatest `collected_at`.
3. Invalid JSONL lines abort reconcile before SQLite mutation for that line.
4. `facts.staging.json` exists only when schema validation succeeds; failed `stage` leaves no staging file.
5. `total_fact_keys` in staging equals `SELECT COUNT(*) FROM fact_snapshots`.
6. `changed_key_count` in export equals `SELECT COUNT(DISTINCT inventory_uuid || char(9) || fact_key) FROM fact_diffs WHERE run_id = R`.
7. Running `facts-chain reconcile` a second time with the same `J` and `R` does not increase `fact_diffs` row count for `R`.
8. `changed_keys_digest` matches SHA-256 of sorted `inventory_uuid\tfact_key` pairs from `fact_diffs` for `R`.

Operators may query invariants directly with `sqlite3 /app/state/facts.db`.
