use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
struct RawLine {
    op: String,
    key: String,
    #[serde(default)]
    value: String,
}

#[derive(Debug, Clone)]
pub enum BatchOp {
    Put { key: String, value: String },
    Delete { key: String },
}

pub fn parse_batch_file(path: &Path) -> Result<Vec<BatchOp>, String> {
    let raw = fs::read_to_string(path).map_err(|e| format!("read batch: {e}"))?;
    let mut ops = Vec::new();
    for line in raw.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let row: RawLine = serde_json::from_str(trimmed).map_err(|e| format!("jsonl: {e}"))?;
        match row.op.as_str() {
            "put" => ops.push(BatchOp::Put {
                key: row.key,
                value: row.value,
            }),
            "delete" => ops.push(BatchOp::Delete { key: row.key }),
            other => return Err(format!("unknown op: {other}")),
        }
    }
    Ok(ops)
}
