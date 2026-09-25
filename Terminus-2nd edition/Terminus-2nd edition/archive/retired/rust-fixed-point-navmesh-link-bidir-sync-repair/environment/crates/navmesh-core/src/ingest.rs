use crate::model::MeshBundle;
use std::fs;
use std::path::Path;

pub fn load_mesh(mesh_path: &Path) -> Result<MeshBundle, String> {
    let raw = fs::read_to_string(mesh_path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
