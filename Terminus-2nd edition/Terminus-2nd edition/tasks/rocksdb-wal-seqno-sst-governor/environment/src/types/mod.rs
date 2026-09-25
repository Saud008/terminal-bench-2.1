use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct WalPut {
    pub key: String,
    pub value: String,
    pub seqno: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PointTombstone {
    pub key: String,
    pub seqno: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct WalBatchInput {
    pub batch_id: String,
    pub seqno: u64,
    pub committed: bool,
    pub cf: String,
    pub puts: Vec<WalPut>,
    pub point_tombstones: Vec<PointTombstone>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SstKey {
    pub key: String,
    pub value: String,
    pub seqno: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RangeTombstone {
    pub start: String,
    pub end: String,
    pub seqno: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergeOperand {
    pub key: String,
    pub operands: Vec<String>,
    pub partial_value: String,
    pub finalized: bool,
    pub seqno: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SstFileInput {
    pub file_id: String,
    pub cf: String,
    pub level: u32,
    pub size_bytes: u64,
    pub min_seqno: u64,
    pub max_seqno: u64,
    pub keys: Vec<SstKey>,
    pub point_tombstones: Vec<PointTombstone>,
    pub range_tombstones: Vec<RangeTombstone>,
    pub merge_operands: Vec<MergeOperand>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ManifestInput {
    pub snapshot_seqno: u64,
    pub watermark_seqno: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct WalBatchRow {
    pub batch_id: String,
    pub seqno: u64,
    pub committed: bool,
    pub cf: String,
    pub puts: Vec<WalPut>,
    pub point_tombstones: Vec<PointTombstone>,
    pub source: String,
    pub ingest_order: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SstFileRow {
    pub file_id: String,
    pub cf: String,
    pub level: u32,
    pub size_bytes: u64,
    pub min_seqno: u64,
    pub max_seqno: u64,
    pub keys: Vec<SstKey>,
    pub point_tombstones: Vec<PointTombstone>,
    pub range_tombstones: Vec<RangeTombstone>,
    pub merge_operands: Vec<MergeOperand>,
    pub source: String,
    pub ingest_order: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StageFile {
    pub ingest_seq: u32,
    pub snapshot_seqno: u64,
    pub watermark_seqno: u64,
    pub wal_batches: Vec<WalBatchRow>,
    pub sst_files: Vec<SstFileRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct VisibleKey {
    pub key: String,
    pub value: String,
    pub seqno: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GovernorReport {
    pub snapshot_seqno: u64,
    pub watermark_seqno: u64,
    pub selected_sst: Vec<String>,
    pub visible_keys: BTreeMap<String, Vec<VisibleKey>>,
    pub reclaimed_bytes: u64,
    pub compact_pass: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CompactState {
    pub reclaimed_bytes: u64,
    pub compact_pass: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KeyRecord {
    pub cf: String,
    pub key: String,
    pub value: String,
    pub seqno: u64,
    pub kind: RecordKind,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RecordKind {
    Put,
    PointTombstone,
    RangeTombstone,
    Merge,
}
