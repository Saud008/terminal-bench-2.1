use crate::feed_tiebreak;
use crate::feed_cache_store;
use crate::types::{Config, GenerationActive, OverlapGeneration, FeedCacheSnapshot};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn run_stage(cfg: &Config, seed: &str, bundle: &str) -> Result<(), String> {
    let snap = feed_cache_store::read_snapshot(&cfg.feed_cache_path)?;
    feed_cache_store::validate_seed_bundle(&snap, seed, bundle)?;
    let reconcile_id = scoped_run_id(seed, bundle, snap.load_generation);
    let active = GenerationActive {
        seed: seed.to_string(),
        bundle: bundle.to_string(),
        reconcile_id,
        load_generation: snap.load_generation,
    };
    write_ledger(&cfg.generation_path, active)
}

pub fn read_active(cfg: &Config) -> Result<GenerationActive, String> {
    let ledger = read_ledger(&cfg.generation_path)?;
    ledger.active.ok_or_else(|| "no active reconcile row".into())
}

pub fn network_rows(snap: &FeedCacheSnapshot) -> Vec<crate::types::StagedRecord> {
    feed_tiebreak::resolve_records(&snap.records)
}

fn scoped_run_id(seed: &str, bundle: &str, seq: u64) -> String {
    let mut hasher = Sha256::new();
    hasher.update(format!("{seed}:{bundle}:{seq}"));
    let digest = hex::encode(hasher.finalize());
    format!("merge-{}", &digest[..12])
}

fn read_ledger(path: &str) -> Result<OverlapGeneration, String> {
    if !Path::new(path).exists() {
        return Ok(OverlapGeneration { active: None });
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn write_ledger(path: &str, active: GenerationActive) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let ledger = OverlapGeneration {
        active: Some(active),
    };
    let data = serde_json::to_string_pretty(&ledger).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
