pub mod decoy;
pub mod export;
pub mod ingest;
pub mod relayout;
pub mod staging;
pub mod types;
pub mod vtable;

pub const DEFAULT_LEDGER_PATH: &str = "/app/state/vtable-ledger.bin";
pub const DEFAULT_RELAYOUT_PATH: &str = "/app/output/relayout.wire";
pub const DEFAULT_SEAL_PATH: &str = "/app/output/wire-seal.txt";

pub const GAP_MAGIC: &[u8; 4] = b"GAPS";
pub const MULTI_ROOT_MAGIC: &[u8; 4] = b"MR2R";
pub const LEDGER_MAGIC: &[u8; 4] = b"FBLE";
