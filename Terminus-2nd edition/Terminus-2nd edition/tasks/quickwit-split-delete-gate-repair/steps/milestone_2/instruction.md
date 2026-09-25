Milestone 2 adds delete-by-query gating, doc store GC ordering, and search consistency after index, delete, merge, and search. Milestone 1 merge metadata and checkpoint behaviors must remain correct.

Split publish must follow /app/docs/split-scheduler.md and /app/docs/delete-gate.md: pending delete tombstones apply before manifest append and doc materialization. Delete processing must open the inverted-index delete gate before doc store GC runs. Search output at /app/state/search-report.json must match /app/docs/search-consistency.md after the full pipeline.

Run index, split publish, delete, merge, and search via qwindex subcommands documented in /app/docs/cli.md. Rebuild the binary after changes under /app/crates/. When TB3_DOCS_DIR points at an absolute fixture directory, index loads batches identically to /app/fixtures/docs/.
