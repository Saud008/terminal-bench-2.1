use crate::yard_model::ScenarioFile;
use crate::scenario_root;
use std::path::PathBuf;

pub fn scenario_path(name: &str) -> PathBuf {
    PathBuf::from(format!("{}/{}.json", scenario_root(), name))
}

pub fn load_scenario(path: &std::path::Path) -> Result<ScenarioFile, String> {
    let raw = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn validate_scenario(sf: &ScenarioFile, expected: &str) -> Result<(), String> {
    if sf.scenario_id != expected {
        return Err("scenario_id mismatch".into());
    }
    Ok(())
}

pub fn bus_ids(sf: &ScenarioFile) -> Vec<String> {
    let mut ids: Vec<String> = sf.buses.iter().map(|b| b.bus_id.clone()).collect();
    ids.sort();
    ids
}
