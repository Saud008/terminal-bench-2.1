Implement the disk-backed staging pipeline for the promingest remote-write service at /app/cmd/promingest. The HTTP server accepts Snappy-compressed remote-write blocks and must persist each accepted write under /app/data/ingest before snapshot export can read it back through relabel and exemplar binding stages.

The service listens on 127.0.0.1:9090. Block layout, native histogram handling, exemplar binding, relabel deduplication, staging file format, and export ordering are defined in /app/docs/remote-write.md, /app/docs/native-histogram.md, /app/docs/exemplar-binding.md, /app/docs/relabel-rules.md, /app/docs/staging-ingest.md, and /app/docs/contract.md.

Complete the ingest and export workflow under /app/internal/ so rebuilt binaries honor every contract. The normalize helper under /app/internal/normalize/ is experimental and is not authoritative for production export. Do not edit /app/docs/, /app/fixtures/, or files under /tests/.
