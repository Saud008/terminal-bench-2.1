pub mod collision;
pub mod decoy;
pub mod demux;
pub mod export;
pub mod io;
pub mod lane;
pub mod stage;
pub mod staging;
pub mod types;

pub const DEFAULT_STAGING_PATH: &str = "/app/state/lane-read-staging.json";
pub const DEFAULT_LEDGER_PATH: &str = "/app/state/umi-demux-ledger.json";
pub const DEFAULT_ATLAS_PATH: &str = "/app/output/umi-collision-atlas.json";
pub const DEFAULT_DIGEST_PATH: &str = "/app/output/atlas-digest.txt";
