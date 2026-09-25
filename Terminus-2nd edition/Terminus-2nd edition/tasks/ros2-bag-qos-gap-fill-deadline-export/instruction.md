The bag-audit CLI at /usr/local/bin/bag-audit replays simplified rosbag2 bundles from /app/fixtures/bags/ through gap fill, deadline scanning, and SQLite export, but the Rust modules under /app/crates/bag-audit/src/ produce wrong exports. Repair those sources so bag-audit audit matches the pipeline wired in /app/crates/bag-audit/src/pipeline.rs for every bag id in /app/fixtures/catalog.json and every seed in /app/fixtures/seeds.json.

Bag layout, gap-fill rules, QoS deadline evaluation, and SQLite columns are defined in /app/docs/bag-format.md, /app/docs/gap-fill-rules.md, /app/docs/qos-deadline.md, and /app/docs/export-schema.md. Payload decoding must use each JSONL line raw topic before remap; exported rows store the canonical topic after remap.

Change only Rust sources under /app/crates/bag-audit/src/. Do not edit /app/docs/, /app/fixtures/, or /tests/. The environment is offline; Rust and Cargo are on PATH (see /app/README.md).
