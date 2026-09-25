The mantidx CLI under /app simulates an RT search index with RAM segments, disk rotate, killlists, and binlog checkpoints. Milestone 1 asks you to implement rotate ordering, binlog checkpoint commit during rotate, and rotate audit metadata in the Rust core.

Implement rotate and binlog handling so behavior matches /app/docs/rotate-metadata.md and /app/docs/binlog-checkpoint.md. State files under /app/state/ include rotate-meta.json, rotate-audit.json, binlog-checkpoint.json, and killlist.json.

Rebuild with cargo build --release --bin mantidx from /app. Subcommands are in /app/docs/cli.md. When TB3_DOCS_DIR is set to an absolute directory, insert --batch accepts files from that directory the same as /app/fixtures/docs/. Do not edit /app/docs/, /app/fixtures/, or /opt/verifier-fixtures/.
