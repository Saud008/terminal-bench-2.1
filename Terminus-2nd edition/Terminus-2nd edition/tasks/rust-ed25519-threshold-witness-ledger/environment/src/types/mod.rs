use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuorumSpec {
    pub threshold: u32,
    pub total: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyDoc {
    pub release_id: String,
    pub quorum: QuorumSpec,
    pub artifact_file: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyEntry {
    pub keyid: String,
    pub scheme: String,
    pub public: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevocationRow {
    pub keyid: String,
    pub revoked_epoch: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WitnessRow {
    pub witness_id: String,
    pub release_id: String,
    pub artifact_digest: String,
    pub epoch: u64,
    pub prior_witness_id: Option<String>,
    pub signer_keyid: String,
    pub signature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagingDoc {
    pub ingest_seq: u64,
    pub bundle_dir: String,
    pub policy: PolicyDoc,
    pub artifact_digest: String,
    pub keys: BTreeMap<String, KeyEntry>,
    pub revocations: Vec<RevocationRow>,
    pub witnesses: Vec<WitnessRow>,
    pub replay_deduped: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WitnessOutcome {
    pub witness_id: String,
    pub signature_ok: bool,
    pub provenance_ok: bool,
    pub revoked_signer: bool,
    pub counts_toward_quorum: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerifyResult {
    pub epoch: u64,
    pub quorum_met: bool,
    pub valid_witness_count: u32,
    pub threshold: u32,
    pub provenance_ok: bool,
    pub replay_deduped: u32,
    pub witnesses: Vec<WitnessOutcome>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerWitnessRow {
    pub witness_id: String,
    pub signer_keyid: String,
    pub epoch: u64,
    pub prior_witness_id: String,
    pub counts_toward_quorum: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerDoc {
    pub release_id: String,
    pub artifact_digest: String,
    pub epoch: u64,
    pub quorum_met: bool,
    pub valid_witness_count: u32,
    pub threshold: u32,
    pub ingest_seq: u64,
    pub witnesses: Vec<LedgerWitnessRow>,
    pub ledger_digest: String,
}
