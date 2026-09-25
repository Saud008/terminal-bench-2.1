//! Ingest stage: XML parse, merge, and staging snapshot writers.

pub use crate::parse::{load_merged, parse_config, parse_str};
pub use crate::staging::{build_stage, save_stage, DEFAULT_STAGE_PATH};
