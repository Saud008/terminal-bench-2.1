use crate::tasking_types::ScenarioBundle;
use std::fs;
use std::path::Path;

pub fn read_scenario(path: &Path) -> Result<ScenarioBundle, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
