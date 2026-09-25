use std::path::Path;

use crate::archive_rebuild::legacy;
use crate::ruby::RubyCue;
use crate::ssrrn_staging;

pub struct StagedExportInput {
    pub fixture: String,
    pub seed: String,
    pub seed_offset_ms: u32,
    pub parsed_count: u32,
    pub overlap_trims: u32,
    pub ruby_shifts: u32,
    pub cues: Vec<RubyCue>,
}

pub fn load_staged_export_input(
    snapshot_path: &Path,
    input_path: &Path,
    seed: &str,
    _expected_export_seq: u32,
) -> StagedExportInput {
    let snapshot = ssrrn_staging::read_snapshot(snapshot_path);
    let cues = legacy::build_ruby_cues(input_path, seed);
    StagedExportInput {
        fixture: snapshot.fixture,
        seed: snapshot.seed,
        seed_offset_ms: snapshot.seed_offset_ms,
        parsed_count: snapshot.parsed_count,
        overlap_trims: snapshot.overlap_trims,
        ruby_shifts: snapshot.ruby_shifts,
        cues,
    }
}
