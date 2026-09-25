use crate::attest_model::{MetadataEntry, MetadataRegistry};
use std::fs;

pub fn load_registry(path: &str) -> Result<MetadataRegistry, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn lookup<'a>(reg: &'a MetadataRegistry, aaguid: &str) -> Option<&'a MetadataEntry> {
    let key = aaguid.replace('-', "").to_uppercase();
    reg.entries.get(&key)
}
