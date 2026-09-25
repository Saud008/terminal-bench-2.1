pub mod attest;
pub mod canonicalize;
pub mod decoy_wrap;
pub mod export;
pub mod ledger;
pub mod load;
pub mod parse;
pub mod resolve;
pub mod types;

pub const DEFAULT_LEDGER_PATH: &str = "/app/state/import-alias.bin";
pub const DEFAULT_EXPORT_PATH: &str = "/app/output/component-attestation.json";

pub const CWRC_MAGIC: &[u8; 4] = b"CWRC";
pub const LEDGER_MAGIC: &[u8; 4] = b"IAL1";

pub const EXPORT_KIND_FUNC: u8 = 1;
pub const EXPORT_KIND_INSTANCE: u8 = 2;
