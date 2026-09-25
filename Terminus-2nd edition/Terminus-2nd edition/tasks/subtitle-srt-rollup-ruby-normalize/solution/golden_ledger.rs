use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::ssrrn_staging;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct NormalizeLedger {
    pub version: u32,
    pub fixture: String,
    pub seed: String,
    pub input_digest: String,
    pub snapshot_digest: String,
    pub export_seq: u32,
}

pub fn ledger_path(fixture: &str, seed: &str) -> PathBuf {
    ssrrn_staging::snapshot_dir(fixture, seed).join("normalize-ledger.json")
}

fn export_seq_marker(fixture: &str, seed: &str) -> PathBuf {
    ssrrn_staging::snapshot_dir(fixture, seed).join("export-seq.marker")
}

fn read_marker(fixture: &str, seed: &str) -> u32 {
    fs::read_to_string(export_seq_marker(fixture, seed))
        .ok()
        .and_then(|raw| raw.trim().parse::<u32>().ok())
        .unwrap_or(0)
}

pub fn planned_export_seq(fixture: &str, seed: &str) -> u32 {
    read_marker(fixture, seed) + 1
}

pub fn commit_export_seq(fixture: &str, seed: &str, seq: u32) {
    let marker = export_seq_marker(fixture, seed);
    if let Some(parent) = marker.parent() {
        fs::create_dir_all(parent).expect("create export-seq dir");
    }
    fs::write(&marker, format!("{seq}\n")).expect("write export-seq marker");
}

pub fn write(
    snapshot_path: &Path,
    fixture: &str,
    seed: &str,
    input_digest: &str,
    export_seq: u32,
) -> PathBuf {
    let path = ledger_path(fixture, seed);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).expect("create ledger dir");
    }
    let payload = NormalizeLedger {
        version: 1,
        fixture: fixture.to_string(),
        seed: seed.to_string(),
        input_digest: input_digest.to_string(),
        snapshot_digest: ssrrn_staging::snapshot_body_digest(snapshot_path),
        export_seq,
    };
    let json = serde_json::to_string_pretty(&payload).expect("serialize ledger");
    fs::write(&path, format!("{json}\n")).expect("write ledger");
    path
}

pub fn load(path: &Path) -> Option<NormalizeLedger> {
    let bytes = fs::read(path).ok()?;
    serde_json::from_slice(&bytes).ok()
}

pub fn validate(snapshot_path: &Path, ledger_path: &Path, expected_export_seq: u32) -> bool {
    let ledger = match load(ledger_path) {
        Some(doc) => doc,
        None => return false,
    };
    let snapshot = ssrrn_staging::read_snapshot(snapshot_path);
    ledger.fixture == snapshot.fixture
        && ledger.seed == snapshot.seed
        && ledger.input_digest == snapshot.input_digest
        && ledger.snapshot_digest == ssrrn_staging::snapshot_body_digest(snapshot_path)
        && ledger.export_seq == expected_export_seq
}
