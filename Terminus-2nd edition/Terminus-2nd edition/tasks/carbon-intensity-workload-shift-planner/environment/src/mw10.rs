use crate::mw11::ScenarioMeta;
use std::fs;
use std::path::Path;

pub fn latch_scenario(path: &Path) -> Result<ScenarioMeta, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
