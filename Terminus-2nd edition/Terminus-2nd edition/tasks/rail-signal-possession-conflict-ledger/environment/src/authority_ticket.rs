use crate::rail_model::{Config, PossessionGeneration};
use std::fs;
use std::path::Path;

pub fn run_stage(cfg: &Config, seed: &str, scenario: &str) -> Result<(), String> {
    let snap = crate::topo_persist::read_snapshot(&cfg.trackgraph_cache_path)?;
    crate::topo_persist::validate_seed_scenario(&snap, seed, scenario)?;
    let pid = crate::ledger_emit::possession_id(seed, scenario, snap.load_seq);
    let row = PossessionGeneration {
        seed: seed.to_string(),
        scenario: scenario.to_string(),
        possession_id: pid,
        load_seq: snap.load_seq,
        active: true,
    };
    write_generation(&cfg.possession_gen_path, &row)
}

fn write_generation(path: &str, row: &PossessionGeneration) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(row).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}

pub fn read_generation(path: &str) -> Result<PossessionGeneration, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
