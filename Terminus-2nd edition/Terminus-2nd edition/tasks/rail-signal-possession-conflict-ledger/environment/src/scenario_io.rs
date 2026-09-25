use crate::rail_model::ScenarioFile;
use std::fs;
use std::path::Path;

pub fn scenario_path(name: &str) -> String {
    let root = crate::scenario_root();
    format!("{root}/{name}.json")
}

pub fn load_scenario(path: &str) -> Result<ScenarioFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn block_ids(sf: &ScenarioFile) -> Vec<String> {
    let mut ids: Vec<String> = sf.blocks.iter().map(|b| b.block_id.clone()).collect();
    ids.sort();
    ids
}

pub fn validate_scenario(sf: &ScenarioFile, name: &str) -> Result<(), String> {
    if sf.scenario_id != name {
        return Err("scenario_id mismatch".into());
    }
    Ok(())
}

pub fn read_bytes(path: &Path) -> Result<String, String> {
    fs::read_to_string(path).map_err(|e| e.to_string())
}
