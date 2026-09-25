use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TermPosting {
    pub field: String,
    pub term: String,
    pub freq: u32,
    pub deleted_hits: u32,
    pub norm: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SegmentRow {
    pub segment_id: String,
    pub max_doc: u32,
    pub delete_bits: Vec<u32>,
    pub terms: Vec<TermPosting>,
    pub source: String,
    pub ingest_order: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StageFile {
    pub ingest_seq: u32,
    pub segments: Vec<SegmentRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergedTerm {
    pub field: String,
    pub term: String,
    pub freq: u32,
    pub norm: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SegmentStats {
    pub live_max_doc: u32,
    pub delete_bits: Vec<u32>,
    pub terms: Vec<MergedTerm>,
    pub merge_pass: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergeState {
    pub delete_bits: Vec<u32>,
    pub merge_pass: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SegmentInput {
    pub segment_id: String,
    pub max_doc: u32,
    pub delete_bits: Vec<u32>,
    pub terms: Vec<TermPosting>,
}
