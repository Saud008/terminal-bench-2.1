# Repair scope

Agent-editable Rust sources for this repair:

- /app/crates/ts-tokenize/src/token_dedupe.rs
- /app/crates/ts-fuzzy/src/prefix_score.rs
- /app/crates/ts-ranker/src/tiebreak.rs
- /app/crates/ts-facet/src/counter.rs
- /app/crates/search-export/src/search_stage.rs
- /app/crates/ingest-stage/src/store.rs

Optional helpers may be edited for compilation, but CLI entrypoints, ts-types models, decoy typo_wrap, and documentation fixtures must stay unchanged.
