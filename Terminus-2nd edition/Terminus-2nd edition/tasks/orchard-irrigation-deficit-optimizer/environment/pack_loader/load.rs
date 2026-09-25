use crate::field_schema::OrchardMeta;
use std::fs;
use std::path::Path;

pub fn load_orchard(path: &Path) -> Result<OrchardMeta, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
