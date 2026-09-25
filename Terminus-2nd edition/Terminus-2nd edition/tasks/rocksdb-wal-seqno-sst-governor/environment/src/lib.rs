pub mod decoy;
pub mod compaction;
pub mod export;
pub mod ingest;
pub mod merge;
pub mod staging;
pub mod types;
pub mod wal;
pub mod witness;

pub const DEFAULT_STAGE_PATH: &str = "/app/state/rocksdb-stage.json";
pub const DEFAULT_COMPACT_STATE_PATH: &str = "/app/state/compact-state.json";
pub const DEFAULT_GOVERNOR_PATH: &str = "/app/output/fab-lsm-governor.json";
pub const DEFAULT_CHECKSUM_PATH: &str = "/app/output/compaction-checksum.txt";
