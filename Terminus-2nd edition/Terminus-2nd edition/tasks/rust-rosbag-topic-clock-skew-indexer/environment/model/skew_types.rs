use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub manifest_latch_dir: String,
    pub timeline_ledger_dir: String,
    pub sync_lattice_dir: String,
    pub drift_min_samples: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TopicSpec {
    pub name: String,
    pub r#type: String,
    pub expected_rate_hz: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestLatch {
    pub bag_id: String,
    pub reference_topic: String,
    pub sync_window_ns: u64,
    pub topic_remap: std::collections::BTreeMap<String, String>,
    pub topics: Vec<TopicSpec>,
    pub manifest_revision: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MsgRow {
    pub topic: String,
    pub seq: u64,
    pub header_stamp_ns: u64,
    pub receive_stamp_ns: u64,
    pub relay_pass: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncPair {
    pub ref_stamp_ns: u64,
    pub topic: String,
    pub header_stamp_ns: u64,
    pub delta_ns: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DriftRow {
    pub topic: String,
    pub slope: f64,
    pub intercept_ns: f64,
    pub sample_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkewAtlas {
    pub bag_id: String,
    pub reference_topic: String,
    pub sync_window_ns: u64,
    pub drop_count: u32,
    pub sync_pair_count: u32,
    pub drift_rows: Vec<DriftRow>,
    pub audit_digest: String,
}
