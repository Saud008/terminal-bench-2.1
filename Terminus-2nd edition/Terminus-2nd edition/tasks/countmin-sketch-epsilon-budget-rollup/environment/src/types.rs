use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct UpdateRow {
    pub key: String,
    pub count: u64,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct ShardFile {
    pub shard_id: String,
    pub hash_seed: u64,
    pub width: usize,
    pub depth: usize,
    pub epsilon: f64,
    pub namespace_salt: String,
    pub window_start_ms: u64,
    pub window_end_ms: u64,
    pub updates: Vec<UpdateRow>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct BundleManifest {
    pub bundle_id: String,
    pub query_keys: Vec<String>,
    pub shards: Vec<ShardRef>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct ShardRef {
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EpsilonLineage {
    pub raw_epsilons: Vec<f64>,
    pub composed_epsilon: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StageSnapshot {
    pub engine: String,
    pub bundle_id: String,
    pub hash_seed: u64,
    pub width: usize,
    pub depth: usize,
    pub namespace_salt: String,
    pub overlap_ms: u64,
    pub window_weights: std::collections::BTreeMap<String, f64>,
    pub shard_fingerprints: Vec<String>,
    pub epsilon_lineage: EpsilonLineage,
    pub merge_generation: u64,
    pub query_keys: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub merged_counters: Option<Vec<Vec<u64>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportRollup {
    pub bundle_id: String,
    pub merge_generation: u64,
    pub overlap_ms: u64,
    pub estimates: std::collections::BTreeMap<String, u64>,
    pub epsilon_lineage: EpsilonLineage,
    pub stage_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GenerationFile {
    pub merge_generation: u64,
}

pub fn seed_offset(seed: &str) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in seed.as_bytes() {
        h ^= *b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}
