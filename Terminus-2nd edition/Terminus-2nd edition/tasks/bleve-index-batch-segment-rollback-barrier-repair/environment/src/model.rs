use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchRecord {
    pub id: String,
    pub key: String,
    pub payload: String,
    pub checksum: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SegmentRecord {
    pub doc_id: u64,
    pub id: String,
    pub key: String,
    pub payload: String,
    pub checksum: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SegmentData {
    pub segment_id: u64,
    pub records: Vec<SegmentRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct RootMap {
    pub segments: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct IndexMeta {
    pub next_doc_id: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchSnapshot {
    pub index: String,
    pub batch_path: String,
    pub record_count: usize,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CollatorConfig {
    pub locale: String,
    pub key_order: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportManifest {
    pub index: String,
    pub doc_count: usize,
    pub segments: Vec<String>,
    pub ordered_keys: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct Collator {
    pub rank_map: HashMap<String, usize>,
}
