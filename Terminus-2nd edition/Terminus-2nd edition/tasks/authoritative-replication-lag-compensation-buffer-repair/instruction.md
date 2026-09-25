The `replag-sim` binary under `/app` produces wrong authoritative replication-lag compensation results on bundled tick traces. Sim reports show incorrect lag estimates and buffer counts; ingest manifests report the wrong read head after late frames; snapshot export bundles miss gap fills or break integrity fields.

Repair the Rust modules so `replag-sim ingest`, `simulate`, and `export-snapshot` match the contracts in `/app/docs/` (see `/app/docs/lag-estimator.md`, `/app/docs/input-buffer.md`, `/app/docs/trace-ingest.md`, `/app/docs/input-ledger.md`, `/app/docs/reconnect.md`, `/app/docs/sim-report.md`, `/app/docs/snapshot-merge.md`, and `/app/docs/snapshot-export.md`).

After ingest on `/app/fixtures/traces/baseline_ingest.jsonl` and simulate on `/app/fixtures/traces/baseline_sim.jsonl`, `/app/state/sim-report.json` must report `lag_method` `ewma`, a smoothed (not mean) `lag_estimate_us`, `buffered_inputs_applied` 1, `duplicate_inputs_skipped` 1, `late_frames_rejected` 1, and `read_head` 5. Ingest must write `/app/state/ingest-manifest.json` with `read_head` 5. Run ingest before export; `export-snapshot` must write `/app/output/snapshot-bundle.json` and `/app/state/export-audit.json` with gap-aware merged snapshots and matching integrity fields.

When `TB3_TICK_RATE_HZ` is set, simulate must honor it when `--tick-rate` is zero. When `TB3_TRACE_DIR` points at an absolute directory containing `baseline_sim.jsonl` or `baseline_ingest.jsonl`, simulate and ingest must accept those basename paths. Build a release binary invocable as `replag-sim`.

Do not modify `/app/docs/`, `/app/fixtures/`, or `/opt/verifier-fixtures/`.
