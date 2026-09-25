Milestone 2 extends the mantidx RT index lab under /app. With rotate and binlog behavior from milestone 1 in place, implement killlist merge ordering, RAM segment merge deleted bitmap handling, attribute updates on killed documents, and search consistency in the Rust core.

Behavior must match /app/docs/killlist-merge.md, /app/docs/ram-segment-merge.md, /app/docs/attribute-updates.md, and /app/docs/search-consistency.md. Continue using state under /app/state/ and rebuild with cargo build --release --bin mantidx.

Subcommands remain in /app/docs/cli.md. Hidden verifier batches under /opt/verifier-fixtures/mantidx/hidden/ load through TB3_DOCS_DIR the same as milestone 1. Do not edit bundled docs or fixtures.
