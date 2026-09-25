# Repair scope

Agent-editable Rust sources for this repair:

- /app/crates/xapi-wdf/src/collector.rs
- /app/crates/xapi-index/src/cf_table.rs
- /app/crates/xapi-length/src/norm.rs
- /app/crates/xapi-synonym/src/expand.rs
- /app/crates/query-planner/src/or_branch.rs
- /app/crates/ingest-stage/src/store.rs

Optional helpers under xapi-weight, xapi-index, and search-export may be edited for compilation, but CLI entrypoints, xapi-types models, tokenizer utilities, decoy posting helpers, and documentation fixtures must stay unchanged.
