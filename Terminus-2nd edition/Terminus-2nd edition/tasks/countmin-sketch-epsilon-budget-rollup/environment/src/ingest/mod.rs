pub mod validate;

use std::path::{Path, PathBuf};

use sha2::{Digest, Sha256};

use crate::staging;
use crate::types::{seed_offset, BundleManifest, ShardFile, StageSnapshot};
use crate::window;
use crate::privacy;

pub fn run_ingest(seed: &str, bundle_id: &str, fixture_root: &str) -> Result<(), String> {
    let (manifest, shards) = load_bundle(seed, bundle_id, fixture_root)?;
    let first = &shards[0];
    let overlap = window::compute_overlap(&shards)?;
    let weights = window::shard_weights(&shards, overlap.overlap_ms);
    let lineage = privacy::compose_epsilons(shards.iter().map(|s| s.epsilon).collect());
    let fingerprints: Vec<String> = shards.iter().map(|s| shard_fingerprint(s)).collect();
    let snap = StageSnapshot {
        engine: "cms-hash-v2".into(),
        bundle_id: manifest.bundle_id.clone(),
        hash_seed: first.hash_seed,
        width: first.width,
        depth: first.depth,
        namespace_salt: first.namespace_salt.clone(),
        overlap_ms: overlap.overlap_ms,
        window_weights: weights,
        shard_fingerprints: fingerprints,
        epsilon_lineage: lineage,
        merge_generation: 0,
        query_keys: manifest.query_keys.clone(),
        merged_counters: None,
    };
    staging::write_stage(&snap)?;
    validate::check_compatibility(&shards)?;
    if overlap.overlap_ms == 0 {
        return Err("zero overlap window".into());
    }
    Ok(())
}

pub fn load_bundle(
    seed: &str,
    bundle_id: &str,
    fixture_root: &str,
) -> Result<(BundleManifest, Vec<ShardFile>), String> {
    let root = Path::new(fixture_root);
    let manifest_path = root.join("bundles").join(format!("{bundle_id}.json"));
    let text = std::fs::read_to_string(&manifest_path)
        .map_err(|e| format!("read manifest: {e}"))?;
    let mut manifest: BundleManifest =
        serde_json::from_str(&text).map_err(|e| format!("parse manifest: {e}"))?;
    let width_bias: i64 = std::env::var("TB3_WIDTH_BIAS")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(0);
    let mut shards = Vec::new();
    for shard_ref in &manifest.shards {
        let shard_path = resolve_shard_path(root, &shard_ref.path);
        let shard_text = std::fs::read_to_string(&shard_path)
            .map_err(|e| format!("read shard {}: {e}", shard_ref.path))?;
        let mut shard: ShardFile =
            serde_json::from_str(&shard_text).map_err(|e| format!("parse shard: {e}"))?;
        shard.hash_seed = shard.hash_seed.wrapping_add(seed_offset(seed));
        if width_bias != 0 {
            shard.width = ((shard.width as i64) + width_bias).max(8) as usize;
        }
        shards.push(shard);
    }
    if manifest.bundle_id != bundle_id {
        manifest.bundle_id = bundle_id.to_string();
    }
    Ok((manifest, shards))
}

pub fn load_shards_for_bundle(
    seed: &str,
    bundle_id: &str,
    fixture_root: &str,
) -> Result<Vec<ShardFile>, String> {
    load_bundle(seed, bundle_id, fixture_root).map(|(_, s)| s)
}

fn resolve_shard_path(root: &Path, rel: &str) -> PathBuf {
    let p = Path::new(rel);
    if p.is_absolute() {
        p.to_path_buf()
    } else {
        root.join(rel)
    }
}

fn shard_fingerprint(shard: &ShardFile) -> String {
    let mut hasher = Sha256::new();
    hasher.update(shard.shard_id.as_bytes());
    hasher.update(shard.hash_seed.to_le_bytes());
    hasher.update((shard.width as u64).to_le_bytes());
    hasher.update((shard.depth as u64).to_le_bytes());
    hasher.update(shard.namespace_salt.as_bytes());
    hex::encode(hasher.finalize())
}
