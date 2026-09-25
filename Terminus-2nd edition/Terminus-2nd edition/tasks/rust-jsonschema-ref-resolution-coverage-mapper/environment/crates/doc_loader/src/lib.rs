use js_value::{load_json, object_get};
use serde_json::Value;
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

/// Ingest pass: load schema documents from a directory tree for trace staging.
#[derive(Debug, Clone)]
pub struct SchemaDoc {
    pub id: String,
    pub path: PathBuf,
    pub root: Value,
}

pub fn load_directory(dir: &Path) -> Result<Vec<SchemaDoc>, String> {
    let mut paths: Vec<PathBuf> = fs::read_dir(dir)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("json"))
        .collect();
    paths.sort();
    let mut out = Vec::new();
    for path in paths {
        let root = load_json(&path)?;
        let id = if let Some(uri) = object_get(&root, "$id").and_then(|v| v.as_str()) {
            uri.rsplit('/').next().unwrap_or(uri).replace(".json", "")
        } else {
            path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string()
        };
        out.push(SchemaDoc { id, path, root });
    }
    Ok(out)
}
