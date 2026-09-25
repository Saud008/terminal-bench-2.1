# TLS capsule fingerprint index

Under /app, the TLS capsule lab is supposed to turn raw handshake capsules into a rerunnable fingerprint index. Implement ja4idx so the intake subcommand writes normalized session rows to the JSONL state file and the emit subcommand turns only that persisted row store into the final report.

Required output paths
- /app/state/session_ledger.jsonl
- /app/output/session_index.json

This task is about preserving forensic session evidence, not just emitting one JSON file. The intake side must reconstruct fragmented TLS records, infer which endpoint acted as client or server, discard retransmit duplicates, and persist session rows in sorted session_id order. The emit side must reload those persisted rows, derive normalized fingerprint strings, preserve anomaly counts, and produce deterministic output across repeated runs and alternate capsule directories described in the contract docs.

The required product contracts live in /app/docs/capsule_format.md, /app/docs/record_reassembly.md, /app/docs/retransmit_policy.md, /app/docs/session_ledger_schema.md, /app/docs/ja4_canon.md, /app/docs/role_detection.md, /app/docs/session_index_rules.md, /app/docs/hidden_capsule_override.md, and /app/docs/intake_emit_pipeline.md. Rebuild ja4idx with /app/environment/scripts/build_all.sh before invoking the CLI. When an alternate capsule directory is configured per hidden_capsule_override.md, intake and emit must produce the same report shape as bundled runs.

The finished report must keep sessions sorted by session_id, expose accurate role_map entries, emit normalized fingerprint strings, report frame_count and unique_frames consistently, and set totals.session_count to the session row count. Hardcoding the persisted row store or the final report is insufficient because validation rebuilds ja4idx and exercises the CLI through subprocess calls.
