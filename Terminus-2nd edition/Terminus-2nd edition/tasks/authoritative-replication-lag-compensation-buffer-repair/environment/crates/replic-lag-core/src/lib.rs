//! Authoritative replication lag compensation and snapshot pipeline.

pub mod buffer;
pub mod decoy;
pub mod export;
pub mod ingest;
pub mod lag;
pub mod ledger;
pub mod model;
pub mod rollback;
pub mod sim;
pub mod snapshot;
pub mod store;
pub mod trace_path;

pub use export::export_snapshot_bundle;
pub use ingest::ingest_trace;
pub use sim::run_simulation;
