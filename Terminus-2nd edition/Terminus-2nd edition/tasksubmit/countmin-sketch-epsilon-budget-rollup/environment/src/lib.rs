pub mod decoy;
pub mod export;
pub mod ingest;
pub mod merge;
pub mod namespace;
pub mod privacy;
pub mod sketch;
pub mod staging;
pub mod types;
pub mod window;

pub const DEFAULT_STAGE_PATH: &str = "/app/state/cms-merge-stage.json";
pub const DEFAULT_GENERATION_PATH: &str = "/app/state/merge-generation.json";
pub const DEFAULT_FIXTURE_ROOT: &str = "/app/fixtures";
