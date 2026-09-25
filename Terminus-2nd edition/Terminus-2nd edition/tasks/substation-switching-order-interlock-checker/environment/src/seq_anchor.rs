use crate::bus_graph;
use crate::scenario_loader;
use crate::yard_model::{ScenarioFile, YardSnapshot};
use std::fs;
use std::path::Path;

pub fn write_snapshot(path: &str, seed: &str, scenario: &str, sf: &ScenarioFile) -> Result<(), String> {
    let _bundle = crate::yard_bundle::touch_bundle(sf);
    let prev = read_seq(path);
    let snap = YardSnapshot {
        load_seq: prev,
        seed: seed.to_string(),
        scenario: scenario.to_string(),
        buses: scenario_loader::bus_ids(sf),
        breakers: sf.breakers.clone(),
        energized_sources: sf.energized_sources.clone(),
        adjacency: bus_graph::build_adjacency(sf),
    };
    write_json(path, &snap)
}

pub fn read_snapshot(path: &str) -> Result<YardSnapshot, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn validate_seed_scenario(snap: &YardSnapshot, seed: &str, scenario: &str) -> Result<(), String> {
    if snap.seed != seed || snap.scenario != scenario {
        return Err("yard-cache seed/scenario mismatch".into());
    }
    Ok(())
}

fn read_seq(path: &str) -> u64 {
    read_snapshot(path).map(|s| s.load_seq).unwrap_or(0)
}

fn write_json(path: &str, v: &YardSnapshot) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(v).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
