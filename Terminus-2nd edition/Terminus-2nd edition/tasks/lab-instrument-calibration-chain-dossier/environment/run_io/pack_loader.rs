use crate::chain_schema::RunPack;
use std::fs;
use std::path::PathBuf;

pub fn pack_path(pack_name: &str) -> PathBuf {
    let root = crate::fixture_root();
    PathBuf::from(root).join(format!("{pack_name}.json"))
}

pub fn load_pack(path: &PathBuf) -> Result<RunPack, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
