use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TensorSpec {
    pub name: String,
    pub dtype: String,
    pub shape: Vec<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShardSpec {
    pub shard_file: String,
    pub tensors: Vec<TensorSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestDoc {
    pub manifest_id: String,
    pub base_model_hash: String,
    pub expected_base_model_hash: String,
    pub shards: Vec<ShardSpec>,
}

pub fn read_manifest_dir(dir: &Path) -> Result<Vec<ManifestDoc>, String> {
    let mut paths: Vec<_> = fs::read_dir(dir)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("json"))
        .collect();
    paths.sort();
    let mut docs = Vec::new();
    for path in paths {
        let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let doc: ManifestDoc = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
        docs.push(doc);
    }
    Ok(docs)
}
