use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignedDoc {
    pub signed: Value,
    pub signatures: Vec<SignatureRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignatureRow {
    pub keyid: String,
    pub sig: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyVal {
    pub public: String,
    pub expires_epoch: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyEntry {
    pub keytype: String,
    pub keyval: KeyVal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoleSpec {
    pub keyids: Vec<String>,
    pub threshold: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegationRow {
    pub name: String,
    pub paths: Vec<String>,
    pub threshold: u32,
    pub keyids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagingFile {
    pub ingest_seq: u64,
    pub root_version: u64,
    pub targets_version: u64,
    pub snapshot_version: u64,
    pub keys: BTreeMap<String, KeyEntry>,
    pub root_role: RoleSpec,
    pub targets_role: RoleSpec,
    pub delegations: Vec<DelegationRow>,
    pub targets: BTreeMap<String, Value>,
    pub snapshot_targets_version: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetadataVerify {
    pub role: String,
    pub threshold_met: bool,
    pub valid_signatures: u32,
    pub expired_keyids: Vec<String>,
    pub reuse_violations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerifyResult {
    pub epoch: u64,
    pub rotation_ok: bool,
    pub snapshot_link_ok: bool,
    pub metadata: Vec<MetadataVerify>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionRow {
    pub path: String,
    pub allowed: bool,
    pub delegation: Option<String>,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportFile {
    pub epoch: u64,
    pub rotation_ok: bool,
    pub decisions: Vec<DecisionRow>,
    pub audit_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RejectedRow {
    pub path: String,
    pub reason: String,
    pub delegation: Option<String>,
}
