use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CompressorSpec {
    pub id: String,
    #[serde(default)]
    pub level: i64,
    #[serde(default)]
    pub shuffle: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArrayManifest {
    pub name: String,
    pub shape: Vec<u64>,
    pub chunks: Vec<u64>,
    pub dtype: String,
    pub compressor: CompressorSpec,
    pub chunk_keys: Vec<String>,
}

#[derive(Debug)]
pub struct ManifestError;

pub fn load_manifest_bundle(dir: &Path) -> Result<Vec<ArrayManifest>, ManifestError> {
    let mut paths: Vec<_> = fs::read_dir(dir)
        .map_err(|_| ManifestError)?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("json"))
        .collect();
    paths.sort();
    let mut out: Vec<ArrayManifest> = Vec::new();
    for p in paths {
        if p.file_name().and_then(|s| s.to_str()) == Some("axes.json") {
            continue;
        }
        let raw = fs::read_to_string(&p).map_err(|_| ManifestError)?;
        out.push(serde_json::from_str(&raw).map_err(|_| ManifestError)?);
    }
    out.sort_by(|a, b| b.name.cmp(&a.name));
    Ok(out)
}
