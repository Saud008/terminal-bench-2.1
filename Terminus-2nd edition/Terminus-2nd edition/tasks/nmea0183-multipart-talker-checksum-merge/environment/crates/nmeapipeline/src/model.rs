use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ParsedSentence {
    pub raw: String,
    pub talker: String,
    pub sentence: String,
    pub fields: Vec<String>,
    pub is_multipart: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergeGroup {
    pub merge_key: String,
    pub talker: String,
    pub sentence: String,
    pub multipart_total: u32,
    pub fragments_merged: u32,
    pub payload_fields: Vec<String>,
    pub utc_iso: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RejectedLine {
    pub line: String,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergeSnapshot {
    pub groups: Vec<MergeGroup>,
    pub rejected: Vec<RejectedLine>,
    pub snapshot_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergeReport {
    pub groups: Vec<MergeGroup>,
    pub rejected: Vec<RejectedLine>,
    pub snapshot_digest: String,
}
