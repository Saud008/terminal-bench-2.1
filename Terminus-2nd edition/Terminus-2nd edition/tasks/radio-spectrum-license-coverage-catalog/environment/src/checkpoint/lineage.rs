use crate::checkpoint::wal;
use crate::catalog_schema::{Config, CoverageActive, CoverageGeneration};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn run_coverage(cfg: &Config, seed: &str, bundle: &str) -> Result<(), String> {
    let snap = wal::read_snapshot(&cfg.wal_path)?;
    wal::validate_seed_bundle(&snap, seed, bundle)?;
    let atlas_seq_id = scoped_atlas_seq_id(seed, bundle, snap.load_generation);
    let active = CoverageActive {
        seed: seed.to_string(),
        bundle: bundle.to_string(),
        atlas_seq_id,
        load_generation: snap.load_generation,
    };
    write_coverage(&cfg.coverage_path, active)
}

pub fn read_active(cfg: &Config) -> Result<CoverageActive, String> {
    let ledger = read_coverage(&cfg.coverage_path)?;
    ledger.active.ok_or_else(|| "no active coverage row".into())
}

fn scoped_atlas_seq_id(seed: &str, bundle: &str, gen: u64) -> String {
    let mut hasher = Sha256::new();
    hasher.update(format!("{seed}:{bundle}:{gen}"));
    let digest = hex::encode(hasher.finalize());
    format!("seq-{}", &digest[..12])
}

fn read_coverage(path: &str) -> Result<CoverageGeneration, String> {
    if !Path::new(path).exists() {
        return Ok(CoverageGeneration { active: None });
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn write_coverage(path: &str, active: CoverageActive) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let ledger = CoverageGeneration {
        active: Some(active),
    };
    let data = serde_json::to_string_pretty(&ledger).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
