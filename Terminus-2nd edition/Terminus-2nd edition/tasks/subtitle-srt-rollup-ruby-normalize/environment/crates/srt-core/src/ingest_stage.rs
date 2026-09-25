//! Alternate ingest-stage path. Stage 1 uses parser, ssrrn_timeline, ruby, and ssrrn_staging modules on the hot path.

use std::path::Path;

use crate::types::ParsedCue;

pub fn ingest_cues(path: &Path) -> Vec<ParsedCue> {
    crate::parser::parse_file(path)
}
