use crate::tasking_types::ScenarioBundle;
use std::fs;
use std::path::Path;

pub fn write_scenario_bind(token: &str, bundle: &ScenarioBundle) -> Result<(), String> {
    let path = Path::new(crate::VAR_ROOT).join(format!("scenario-bind-{token}.json"));
    fs::write(path, serde_json::to_string_pretty(bundle).unwrap()).map_err(|e| e.to_string())
}
