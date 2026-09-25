# correlation snapshot snapshot schema

        Path: /app/state/shade-correlation/<run_id>.json

        ingest-scenario also appends run_id and readings_digest to /app/state/run-registry.jsonl for cross-run provenance.

Fields: run_id, scenario, readings_digest, correlated bool, rows array, correlation_digest nullable until correlate runs.

Each row after correlate includes batch_id, reading_id, L, a, b, measured_at_epoch, target_L, target_a, target_b, recipe_version, delta_e, drift_class, rework_applied bool.

correlation_digest is sha256 over compact JSON of rows sorted by batch_id then reading_id.
