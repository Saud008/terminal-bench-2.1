//! Bind-stage fixture loader (verifier ingest path).

use crate::hazard_schema::{BindBundle, FireSpec, PolicySpec, RoadsSpec, ShelterSpec, ZoneSpec};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn load_json<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn bind_scenario(scenario_root: &Path, scenario: &str) -> Result<BindBundle, String> {
    let base = scenario_root.join(scenario);
    let zones: Vec<ZoneSpec> = load_json(&base.join("zones.json"))?;
    let fires: Vec<FireSpec> = load_json(&base.join("fires.json"))?;
    let shelters: Vec<ShelterSpec> = load_json(&base.join("shelters.json"))?;
    let roads: RoadsSpec = load_json(&base.join("roads.json"))?;
    let templates: BTreeMap<String, String> = load_json(&base.join("templates.json"))?;
    let policy: PolicySpec = load_json(&base.join("policy.json"))?;
    Ok(BindBundle {
        scenario: scenario.to_string(),
        zones,
        fires,
        shelters,
        roads,
        templates,
        policy,
    })
}
