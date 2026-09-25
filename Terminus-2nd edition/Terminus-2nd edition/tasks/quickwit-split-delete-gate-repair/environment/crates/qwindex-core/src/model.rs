use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub doc_id: i64,
    pub body: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SplitEntry {
    pub split_id: String,
    pub parent_split_id: Option<String>,
    pub doc_count: i64,
    pub publish_seq: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Manifest {
    pub splits: Vec<SplitEntry>,
    pub lineage_root: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Checkpoint {
    pub merge_seq: i64,
    pub last_complete_merge: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MergeAudit {
    pub status: String,
    pub merged_into: String,
    pub sources: Vec<String>,
    pub cache_flushed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeleteAudit {
    pub query: String,
    pub delete_gate_open: bool,
    pub tombstones_applied: bool,
    pub docstore_gc_ran: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SplitMeta {
    pub active_splits: Vec<String>,
    pub publish_seq: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchReport {
    pub query: String,
    pub hit_count: i64,
    pub doc_ids: Vec<i64>,
}
