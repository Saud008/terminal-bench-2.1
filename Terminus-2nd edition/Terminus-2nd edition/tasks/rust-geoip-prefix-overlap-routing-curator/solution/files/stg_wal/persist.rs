use crate::cidr_normalize;
use crate::types::{BundleFile, FeedCacheSnapshot, StagedRecord};
use std::fs;
use std::path::Path;

pub fn write_snapshot(path: &str, seed: &str, bundle: &str, bf: &BundleFile) -> Result<(), String> {
    let prev = read_seq(path);
    let records = materialize(bf);
    let snap = FeedCacheSnapshot {
        load_generation: prev + 1,
        seed: seed.to_string(),
        bundle: bundle.to_string(),
        records,
    };
    write_json(path, &snap)
}

pub fn read_snapshot(path: &str) -> Result<FeedCacheSnapshot, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn validate_seed_bundle(snap: &FeedCacheSnapshot, seed: &str, bundle: &str) -> Result<(), String> {
    if snap.seed != seed || snap.bundle != bundle {
        return Err("feed-cache seed/bundle mismatch".into());
    }
    Ok(())
}

pub fn materialize(bf: &BundleFile) -> Vec<StagedRecord> {
    let mut out = Vec::new();
    for feed in &bf.feeds {
        for rec in &feed.records {
            let cidr = cidr_normalize::normalize_cidr(&rec.cidr).unwrap_or_else(|_| rec.cidr.clone());
            out.push(StagedRecord {
                cidr,
                country: rec.country.clone(),
                asn: rec.asn,
                feed_id: feed.feed_id.clone(),
                lineage_id: rec.lineage_id.clone(),
            });
        }
    }
    out
}

fn read_seq(path: &str) -> u64 {
    read_snapshot(path).map(|s| s.load_generation).unwrap_or(0)
}

fn write_json(path: &str, v: &FeedCacheSnapshot) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(v).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
