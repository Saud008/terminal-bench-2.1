pub mod decoy;
pub mod export;
pub mod ingest;
pub mod merge;
pub mod staging;
pub mod stats;
pub mod types;
pub mod witness;

pub const DEFAULT_STAGE_PATH: &str = "/app/state/tantivy-stage.json";
pub const DEFAULT_MERGE_STATE_PATH: &str = "/app/state/merge-state.json";
pub const DEFAULT_STATS_PATH: &str = "/app/output/segment-stats.json";
pub const DEFAULT_CHECKSUM_PATH: &str = "/app/output/merge-checksum.txt";
