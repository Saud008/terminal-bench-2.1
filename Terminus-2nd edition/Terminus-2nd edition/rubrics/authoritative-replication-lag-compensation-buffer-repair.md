# Platform rubric — authoritative-replication-lag-compensation-buffer-repair

**Task folder:** tasks/authoritative-replication-lag-compensation-buffer-repair/
**Written:** 2026-07-27T00:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

# Rubric 1

Agent rebuilds replag-sim release binary after editing replic-lag-core modules, +2
Agent writes sim-report.json with lag_method ewma and smoothed lag_estimate_us not arithmetic mean, +3
Agent applies compensation buffer only after input_ack events, +3
Agent increments duplicate_inputs_skipped for repeated input_seq in simulate, +3
Agent rejects late frames without shrinking read_head in sim-report, +3
Agent sets rollback_window_ticks to max of prior window, 30, and reconnect rollback_ticks, +3
Agent writes ingest-manifest.json with read_head 5 on bundled baseline ingest trace, +3
Agent honors TB3_TICK_RATE_HZ when simulate --tick-rate is zero, +2
Agent resolves basename traces under TB3_TRACE_DIR for simulate and ingest, +2
Agent leaves /app/docs and /app/fixtures unchanged, +1
Agent uses arithmetic mean for lag_estimate_us while reporting lag_method ewma, -3
Agent applies buffered compensation before input_ack, -3
Agent advances read_head on rejected late frames during ingest, -3
Agent shrinks rollback_window_ticks below reconnect.md minimum on reconnect, -3
Agent edits /app/docs or /app/fixtures to shortcut verification, -3

# Rubric 2

Agent runs ingest before export-snapshot on trace data, +2
Agent exports gap-filled snapshot rows with cumulative state_hash across full seq range, +3
Agent sets gap_fills matching ingest-recorded gap events, +3
Agent writes integrity_chain consistent with integrity_seed and merged_state_hash, +3
Agent writes export-audit.json fields matching snapshot-bundle.json export, +2
Agent keeps simulate EWMA lag and ack-buffer counts correct alongside export path, +2
Agent exports delta rows without gap-fill slots when ingest recorded snapshot_gap events, -3
Agent hardcodes snapshot-bundle.json rows instead of deriving from SQLite deltas, -3
Agent writes mismatched merged_state_hash or integrity_chain between bundle and audit, -3
Agent runs export-snapshot successfully without prior ingest, -3
Agent copies oracle patches from /solution mount instead of repairing replic-lag-core modules, -3
