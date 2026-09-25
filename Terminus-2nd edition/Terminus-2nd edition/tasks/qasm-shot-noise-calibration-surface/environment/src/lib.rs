pub mod decoy;
pub mod parse;
pub mod drift;
pub mod envelope;
pub mod export;
pub mod histogram;
pub mod mitigate;
pub mod provenance;
pub mod stage;
pub mod staging;
pub mod types;

pub const DEFAULT_STAGING_PATH: &str = "/app/state/cal-staging.json";
pub const DEFAULT_LEDGER_PATH: &str = "/app/state/envelope-ledger.json";
pub const DEFAULT_ENVELOPE_PATH: &str = "/app/output/shot-noise-envelope.json";
pub const DEFAULT_DIGEST_PATH: &str = "/app/output/envelope-digest.txt";
