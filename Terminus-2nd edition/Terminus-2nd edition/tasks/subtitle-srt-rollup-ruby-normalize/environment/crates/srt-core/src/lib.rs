mod archive_rebuild;
mod decoy_wrap;
mod export;
mod ingest_stage;
mod ledger;
mod parser;
mod publish;
mod rollup;
mod ruby;
mod runner;
mod ssrrn_staging;
mod ssrrn_timeline;
mod types;

pub use parser::parse_file;
pub use types::{ExportDoc, seed_offset_ms};

use std::path::Path;

pub fn normalize(path: &Path, seed: &str, fixture: &str) -> ExportDoc {
    runner::run_normalize(path, seed, fixture)
}
