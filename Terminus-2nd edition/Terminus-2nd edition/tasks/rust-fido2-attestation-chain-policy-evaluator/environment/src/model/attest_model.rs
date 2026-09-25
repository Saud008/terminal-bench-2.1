use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub transcript_cache_path: String,
    pub policy_bind_path: String,
    pub bundle_dir: String,
    pub metadata_path: String,
    pub policy_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptRow {
    pub credential_id: String,
    pub aaguid: String,
    pub attestation_format: String,
    pub auth_data_hex: String,
    pub sign_count: u32,
    pub cert_chain: Vec<CertLink>,
    pub uv: bool,
    pub chain_ok: bool,
    pub metadata_hit: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CertLink {
    pub subject_fp: String,
    pub issuer_fp: String,
    pub role: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BundleFile {
    pub batch_id: String,
    pub transcripts: Vec<TranscriptInput>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptInput {
    pub credential_id: String,
    pub aaguid: String,
    pub attestation_format: String,
    pub auth_data_hex: String,
    pub sign_count: u32,
    pub cert_chain: Vec<CertLink>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptCache {
    pub run_seq: u64,
    pub batch_id: String,
    pub bundle: String,
    pub rows: Vec<TranscriptRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyBind {
    pub active: Option<PolicyActive>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyActive {
    pub batch_id: String,
    pub policy_name: String,
    pub bind_seq: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyFile {
    pub name: String,
    pub user_verification: String,
    pub allowed_formats: Vec<String>,
    pub reject_duplicate_credential_id: bool,
    pub min_sign_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetadataRegistry {
    pub entries: std::collections::BTreeMap<String, MetadataEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetadataEntry {
    pub aaguid: String,
    pub description: String,
    pub trust_anchor_fp: String,
    pub attestation_formats: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrustDecision {
    pub credential_id: String,
    pub aaguid: String,
    pub trust_level: String,
    pub reasons: Vec<String>,
    pub sign_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrustSummary {
    pub trusted: u32,
    pub untrusted: u32,
    pub rejected: u32,
    pub dedupe_blocked: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrustReport {
    pub batch_id: String,
    pub policy_name: String,
    pub decisions: Vec<TrustDecision>,
    pub summary: TrustSummary,
    pub audit_digest: String,
}
