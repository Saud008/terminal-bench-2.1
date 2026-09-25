use crate::types::LatticeArtifact;
use std::fs;
use std::path::{Path, PathBuf};

fn path_for(dir: &str, campaign_id: &str) -> PathBuf {
    Path::new(dir).join(format!("{campaign_id}.json"))
}

pub fn write_lattice(dir: &str, art: &LatticeArtifact) -> Result<(), String> {
    fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    let p = path_for(dir, &art.campaign_id);
    let body = serde_json::to_string_pretty(art).map_err(|e| e.to_string())?;
    fs::write(p, body + "\n").map_err(|e| e.to_string())
}

pub fn read_lattice(dir: &str, campaign_id: &str) -> Result<LatticeArtifact, String> {
    let p = path_for(dir, campaign_id);
    let raw = fs::read_to_string(&p).map_err(|e| format!("lattice read {}: {e}", p.display()))?;
    serde_json::from_str(&raw).map_err(|e| format!("lattice parse: {e}"))
}

pub fn clear_lattice(dir: &str, campaign_id: &str) -> Result<(), String> {
    let p = path_for(dir, campaign_id);
    if p.exists() {
        fs::remove_file(&p).map_err(|e| e.to_string())?;
    }
    Ok(())
}
