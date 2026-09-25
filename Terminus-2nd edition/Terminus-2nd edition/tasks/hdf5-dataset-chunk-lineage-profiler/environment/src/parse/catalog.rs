use crate::hdclp_types::CatalogFile;
use std::fs;
use std::path::Path;

pub fn load_catalog(dir: &Path) -> Result<CatalogFile, String> {
    let path = dir.join("catalog.s5cat");
    let raw = fs::read_to_string(&path).map_err(|e| format!("read catalog: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse catalog: {e}"))
}

pub fn load_index_bytes(dir: &Path, dataset_path: &str) -> Result<Vec<u8>, String> {
    let safe = dataset_path.trim_start_matches('/').replace('/', "_");
    let path = dir.join("indexes").join(format!("{safe}.s5idx"));
    fs::read(&path).map_err(|e| format!("read index {path:?}: {e}"))
}

pub fn load_mask_bytes(dir: &Path, rel: &str) -> Result<Vec<u8>, String> {
    let path = dir.join(rel);
    fs::read(&path).map_err(|e| format!("read mask {path:?}: {e}"))
}
