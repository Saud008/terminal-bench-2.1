use std::path::Path;

use crate::ledger;
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
    _input_path: &Path,
    _seed: &str,
    expected_export_seq: u32,
) -> StagedExportInput {
    let snapshot = ssrrn_staging::read_snapshot(snapshot_path);
    let ledger_path = ledger::ledger_path(&snapshot.fixture, &snapshot.seed);
    let ledger_doc = ledger::load(&ledger_path).expect("normalize ledger missing");
    assert_eq!(ledger_doc.fixture, snapshot.fixture);
    assert_eq!(ledger_doc.seed, snapshot.seed);
    assert_eq!(ledger_doc.input_digest, snapshot.input_digest);
    assert_eq!(
        ledger_doc.snapshot_digest,
        ssrrn_staging::snapshot_body_digest(snapshot_path),
        "normalize ledger does not seal snapshot"
    );
    assert_eq!(
        ledger_doc.export_seq, expected_export_seq,
        "normalize ledger export_seq mismatch"
    );
    StagedExportInput {
        fixture: snapshot.fixture,
        seed: snapshot.seed,
        seed_offset_ms: snapshot.seed_offset_ms,
        parsed_count: snapshot.parsed_count,
        overlap_trims: snapshot.overlap_trims,
        ruby_shifts: snapshot.ruby_shifts,
        cues: snapshot.cues,
    }
}
