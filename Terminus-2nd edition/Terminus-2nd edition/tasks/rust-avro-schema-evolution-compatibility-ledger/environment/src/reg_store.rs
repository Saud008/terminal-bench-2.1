use crate::pair_eval::{evaluate_pair, PairResult};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct PairSpec {
    pub subject: String,
    pub writer: String,
    pub reader: String,
}

pub fn ingest_pairs(
    schema_root: &Path,
    pairs_path: &Path,
    staging_path: &Path,
) -> Result<(), String> {
    let raw = fs::read_to_string(pairs_path).map_err(|e| e.to_string())?;
    let mut rows: Vec<PairResult> = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let spec: PairSpec = serde_json::from_str(line).map_err(|e| e.to_string())?;
        let writer = schema_root.join(&spec.writer);
        let reader = schema_root.join(&spec.reader);
        rows.push(evaluate_pair(&spec.subject, &writer, &reader)?);
    }
    rows.sort_by(|a, b| a.reader_path.cmp(&b.reader_path));
    let body: Vec<String> = rows
        .into_iter()
        .map(|r| serde_json::to_string(&r).map_err(|e| e.to_string()))
        .collect::<Result<_, _>>()?;
    fs::write(staging_path, format!("{}
", body.join("
"))).map_err(|e| e.to_string())
}

pub fn read_staging(path: &Path) -> Result<Vec<PairResult>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    raw.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).map_err(|e| e.to_string()))
        .collect()
}
