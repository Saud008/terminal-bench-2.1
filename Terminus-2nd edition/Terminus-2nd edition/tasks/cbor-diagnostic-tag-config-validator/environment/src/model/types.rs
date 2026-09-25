use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct DiagnosticTag {
    pub label: String,
    pub tag: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolicyEnvelope {
    pub policy: String,
    pub nonce: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StagingSnapshot {
    pub bundle_id: String,
    pub diagnostic_tags: Vec<DiagnosticTag>,
    pub envelope: PolicyEnvelope,
    pub version: u64,
}
