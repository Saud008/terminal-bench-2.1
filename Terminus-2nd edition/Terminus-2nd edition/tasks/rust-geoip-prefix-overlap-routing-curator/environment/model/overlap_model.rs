use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub feed_cache_path: String,
    pub generation_path: String,
    pub bundle_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrefixRecord {
    pub cidr: String,
    pub country: String,
    pub asn: u32,
    pub lineage_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeedBlock {
    pub feed_id: String,
    pub records: Vec<PrefixRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BundleFile {
    pub bundle_name: String,
    pub feeds: Vec<FeedBlock>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagedRecord {
    pub cidr: String,
    pub country: String,
    pub asn: u32,
    pub feed_id: String,
    pub lineage_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeedCacheSnapshot {
    pub load_generation: u64,
    pub seed: String,
    pub bundle: String,
    pub records: Vec<StagedRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerationActive {
    pub seed: String,
    pub bundle: String,
    pub reconcile_id: String,
    pub load_generation: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverlapGeneration {
    pub active: Option<GenerationActive>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverlapRow {
    pub cidr: String,
    pub country: String,
    pub asn: u32,
    pub winning_feed: String,
    pub contained_by: Option<String>,
    pub asn_lineage: Vec<String>,
    pub reserved_filtered: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverlapSummary {
    pub total_prefixes: u32,
    pub overlap_pairs: u32,
    pub asn_conflicts: u32,
    pub reserved_dropped: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverlapReport {
    pub seed: String,
    pub bundle: String,
    pub reconcile_id: String,
    pub overlap_rows: Vec<OverlapRow>,
    pub summary: OverlapSummary,
    pub audit_digest: String,
}

pub type ManifestMap = BTreeMap<String, String>;
