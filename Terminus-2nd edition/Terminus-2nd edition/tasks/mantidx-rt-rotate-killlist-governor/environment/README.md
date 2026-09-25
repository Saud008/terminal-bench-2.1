# mantidx RT index lab

Simulated RT search index with RAM segments, disk rotate, killlists, and binlog checkpoints.

Contract docs live under /app/docs/. State under /app/state/, database at /app/data/mantidx.db.

Rebuild after source edits:

    cargo build --release --bin mantidx
