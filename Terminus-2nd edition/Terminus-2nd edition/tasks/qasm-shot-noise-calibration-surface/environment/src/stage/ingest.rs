use std::fs;
use std::path::Path;

use crate::staging;
use crate::types::{
    DriftFile, HistogramFile, MitigationFile, SeedManifest, StagingFile,
};

pub fn ingest_calibration(
    cal_dir: &str,
    qasm_path: &str,
    manifest_path: &str,
    staging_path: &str,
) -> Result<(), String> {
    let histogram: HistogramFile = load_json(&Path::new(cal_dir).join("histogram.json"))?;
    let mitigation: MitigationFile =
        load_json(&Path::new(cal_dir).join("mitigation_matrices.json"))?;
    let drift: DriftFile = load_json(&Path::new(cal_dir).join("readout_drift.json"))?;
    let manifest: SeedManifest = load_json(Path::new(manifest_path))?;

    let qasm_raw = fs::read_to_string(qasm_path).map_err(|e| e.to_string())?;
    let gate_count = count_gates(&qasm_raw);

    let prev_seq = staging::load_staging(staging_path)
        .ok()
        .map(|s| s.ingest_seq)
        .unwrap_or(0);

    let staging = StagingFile {
        ingest_seq: prev_seq + 1,
        manifest,
        qasm_gate_count: gate_count,
        histogram,
        mitigation,
        drift,
    };

    staging::save_staging(staging_path, &staging)
}

fn load_json<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn count_gates(qasm: &str) -> u32 {
    qasm.lines()
        .map(|l| l.trim())
        .filter(|l| {
            l.ends_with(';')
                && (l.starts_with('h') || l.starts_with("cx") || l.starts_with("measure"))
        })
        .count() as u32
}
