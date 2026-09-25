use graph_ir::read_graph_dir;
use propagate::{shape_vec_to_json, propagate_graph};
use serde::Serialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, serde::Deserialize, Clone)]
pub struct StagedRow {
    pub graph_id: String,
    pub tensor: String,
    pub shape: Vec<serde_json::Value>,
    pub node_id: String,
    pub ordinal: u32,
}

pub fn batch_dir_load(graph_dir: &Path, staging_path: &Path) -> Result<(), String> {
    let docs = read_graph_dir(graph_dir)?;
    let mut all_rows = Vec::new();
    for doc in docs {
        all_rows.extend(propagate_graph(&doc)?);
    }
    all_rows.sort_by(|a, b| (a.graph_id.as_str(), a.ordinal).cmp(&(b.graph_id.as_str(), b.ordinal)));
    let lines: Vec<String> = all_rows
        .into_iter()
        .map(|row| {
            let staged = StagedRow {
                graph_id: row.graph_id,
                tensor: row.tensor,
                shape: shape_vec_to_json(&row.shape),
                node_id: row.node_id,
                ordinal: row.ordinal,
            };
            serde_json::to_string(&staged).map_err(|e| e.to_string())
        })
        .collect::<Result<_, _>>()?;
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
