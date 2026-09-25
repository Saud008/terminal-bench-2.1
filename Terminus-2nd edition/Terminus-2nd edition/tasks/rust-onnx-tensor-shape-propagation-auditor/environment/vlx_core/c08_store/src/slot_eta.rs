use graph_ir::read_graph_dir;
use propagate::{shape_vec_to_json, propagate_graph};
use serde::Serialize;
use std::fs;
use std::path::Path;

// Ingest path: load graph batch JSON from disk into the staging ledger file.

#[derive(Debug, Serialize, serde::Deserialize, Clone)]
pub struct StagedRow {
    pub graph_id: String,
    pub tensor: String,
    pub shape: Vec<serde_json::Value>,
    pub node_id: String,
    pub ordinal: u32,
}

pub fn dir_load_rows(graph_dir: &Path, staging_path: &Path) -> Result<(), String> {
    let docs = read_graph_dir(graph_dir)?;
    let mut lines = Vec::new();
    for doc in docs {
        for row in propagate_graph(&doc)? {
            let staged = StagedRow {
                graph_id: row.graph_id,
                tensor: row.tensor,
                shape: shape_vec_to_json(&row.shape),
                node_id: row.node_id,
                ordinal: row.ordinal,
            };
            lines.push(serde_json::to_string(&staged).map_err(|e| e.to_string())?);
        }
    }
    lines.sort();
    fs::write(staging_path, format!("{}
", lines.join("
"))).map_err(|e| e.to_string())
}

pub fn read_staging(path: &Path) -> Result<Vec<StagedRow>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    raw.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).map_err(|e| e.to_string()))
        .collect()
}
