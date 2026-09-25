Task identity f7a3c91e defines the engineering problem for fiber splice loss acceptance atlas. See /app/docs/engineering-problem-contract.md for scope boundaries.

Field engineers must publish a deterministic splice acceptance atlas from OTDR lab trace captures, splice plans, connector inventory, and route segment maps before a long-haul span is released. Build fsplatlas on the working Rust baseline under /app to load capture bundles, run numerical calibration of adjacent-sample loss deltas, align reflection events to route milepost intervals using bracket rules in /app/docs/route-segment-binding.md, rank duplicate reflections by capture epoch precedence, reconcile connector pair-loss budgets from inventory against segment ledgers, suppress near-duplicate reflections within tolerance, and publish per-segment acceptance summaries as JSON under /app/output

Install fsplatlas at /app/bin/fsplatlas with subcommands load-capture, scan-reflections, correlate-span, and publish-verdict. Trace manifest fields, sample stream layout, and launch-power normalization follow /app/docs/trace-manifest-schema.md and /app/docs/sample-stream-format.md. Loss event detection thresholds, adjacent-sample delta rules, and reflection marker handling follow /app/docs/loss-event-detection.md. Duplicate reflection suppression within reflection_tolerance_m with epoch precedence follows /app/docs/duplicate-reflection-policy.md. Route milepost bracket binding and connector endpoint attribution follow /app/docs/route-segment-binding.md. Connector inventory pair-loss budgets and cumulative budget ledger rules follow /app/docs/connector-budget-ledger.md. Acceptance verdict rank precedence, summary counters, and audit_digest rules follow /app/docs/acceptance-atlas-fields.md. Capture cache schema and topology-snapshot layout follow /app/docs/capture-cache-schema.md and /app/docs/topology-snapshot-schema.md. Bundled run inventory and fixture behaviors appear in /app/docs/run-catalog.md and /app/docs/pytest-verifier-primitives.md.

fsplatlas load-capture reads trace_manifest.json, splice_plan.json, and segments.json for a run id and writes capture-cache JSON under /app/state/capture-cache/.

fsplatlas scan-reflections reads samples.jsonl against capture-cache thresholds and writes /app/work/reflection-buffer/<run-id>.jsonl.

fsplatlas correlate-span reads reflection-buffer rows, route segments, and connector inventory, materializes /app/work/topology-snapshot/<run-id>.json with per-segment loss totals and budget consumption.

fsplatlas publish-verdict reads topology-snapshot only and writes acceptance atlas JSON to the caller --output path ending with -splice-atlas.json.

Bundled fixtures live under /app/fixtures/. Runtime trace roots honor TB3_TRACE_ROOT. Loss threshold and reflection tolerance overrides honor TB3_LOSS_THRESHOLD_DB and TB3_REFLECTION_TOLERANCE_M.

Compile fsplatlas with cargo build --release --locked from /app and install the binary to /app/bin/fsplatlas. Run /app/scripts/reset-workspace.sh before cross-run verifier cases. The backscatter decoy module is not used by load-capture, scan-reflections, correlate-span, or publish-verdict.

Verifier harness uses tests/splice_refmath.py and hashlib per /app/docs/pytest-verifier-primitives.md and /app/tools/audit_digest_ref.py.
