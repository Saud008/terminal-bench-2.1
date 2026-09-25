use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WheelRow {
    pub tag: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexRow {
    pub package: String,
    pub version: String,
    pub requires_python: Option<String>,
    pub yanked: bool,
    pub wheels: Vec<WheelRow>,
    pub source_id: Option<String>,
}

pub fn load_index(path: &Path) -> Result<Vec<IndexRow>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let mut rows: Vec<IndexRow> = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    // NOTE: index row filter policy
    for r in &mut rows {
        if r.source_id.is_none() {
            r.source_id = Some("primary".into());
        }
    }
    Ok(rows)
}

pub fn union_indices(paths: &[&Path]) -> Result<Vec<IndexRow>, String> {
    let mut all = Vec::new();
    for p in paths {
        all.extend(load_index(p)?);
    }
    Ok(all)
}
