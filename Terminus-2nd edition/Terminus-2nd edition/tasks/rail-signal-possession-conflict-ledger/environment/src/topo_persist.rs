use crate::rail_model::TopoCacheSnapshot;
use crate::adj_walk;
use crate::rail_model::ScenarioFile;
use std::fs;
use std::path::Path;

pub fn write_snapshot(path: &str, seed: &str, scenario: &str, sf: &ScenarioFile) -> Result<(), String> {
    let _load = crate::track_load::load_track_bundle(sf);
    let prev = read_seq(path);
    let blocks = crate::scenario_io::block_ids(sf);
    let zone_map = adj_walk::build_zone_map(sf);
    let snap = TopoCacheSnapshot {
        load_seq: prev,
        seed: seed.to_string(),
        scenario: scenario.to_string(),
        blocks,
        zone_map,
    };
    write_json(path, &snap)
}

pub fn read_snapshot(path: &str) -> Result<TopoCacheSnapshot, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn validate_seed_scenario(snap: &TopoCacheSnapshot, seed: &str, scenario: &str) -> Result<(), String> {
    if snap.seed != seed || snap.scenario != scenario {
        return Err("zone-cache seed/scenario mismatch".into());
    }
    Ok(())
}

fn read_seq(path: &str) -> u64 {
    read_snapshot(path).map(|s| s.load_seq).unwrap_or(0)
}

fn write_json(path: &str, v: &TopoCacheSnapshot) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(v).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
