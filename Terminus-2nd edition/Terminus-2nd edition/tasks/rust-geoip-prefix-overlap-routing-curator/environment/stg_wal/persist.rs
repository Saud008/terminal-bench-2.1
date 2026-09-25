use crate::cidr_normalize;
use crate::types::{BundleFile, FeedCacheSnapshot, StagedRecord};
use std::fs;
use std::path::Path;

/// STUB — implement feed-normalize WAL write per /app/docs/feed-cache-schema.md
/// (advance load_generation from the prior on-disk value).
pub fn write_snapshot(
    _path: &str,
    _seed: &str,
    _bundle: &str,
    _bf: &BundleFile,
) -> Result<(), String> {
    Err("STUB: write_snapshot not implemented".into())
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

/// STUB — normalize each record CIDR before staging per /app/docs/cidr-normalization-contract.md
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

#[allow(dead_code)]
fn read_seq(path: &str) -> u64 {
    read_snapshot(path).map(|s| s.load_generation).unwrap_or(0)
}

#[allow(dead_code)]
fn write_json(path: &str, v: &FeedCacheSnapshot) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(v).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
