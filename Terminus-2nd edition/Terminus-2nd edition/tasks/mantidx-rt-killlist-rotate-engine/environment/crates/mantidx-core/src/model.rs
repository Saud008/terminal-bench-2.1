use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub doc_id: i64,
    pub body: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KillEntry {
    pub doc_id: i64,
    pub segment_id: String,
    pub segment_order: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KilllistState {
    pub pending: Vec<KillEntry>,
    pub applied: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RotateMeta {
    pub active_ram: Vec<String>,
    pub disk_chunks: Vec<String>,
    pub rotate_seq: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinlogCheckpoint {
    pub last_committed_seq: i64,
    pub rotate_seq: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RotateAudit {
    pub disk_published_before_killlist: bool,
    pub killlist_applied: bool,
    pub killlist_applied_on_ram_tier: bool,
    pub disk_chunk_id: String,
    pub checkpoint_seq: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RamSegmentMeta {
    pub segment_id: String,
    pub deleted_bitmap: Vec<i64>,
    pub segment_order: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RamSegmentsFile {
    pub segments: Vec<RamSegmentMeta>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MergeRamAudit {
    pub left: String,
    pub right: String,
    pub merged_into: String,
    pub deleted_respected: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchReport {
    pub query: String,
    pub hit_count: i64,
    pub doc_ids: Vec<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AttributeAudit {
    pub doc_id: i64,
    pub price: i64,
    pub rejected_killed: bool,
}
