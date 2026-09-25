use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawBundle {
    pub bundle_id: String,
    pub fingerprint: String,
    pub packages: Vec<RawPackage>,
    pub edges: Vec<RawEdge>,
    pub binaries: Vec<BinaryRow>,
    pub vulnerabilities: Vec<VulnRow>,
    pub vex: Vec<VexStatement>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawPackage {
    pub purl: String,
    pub name: String,
    pub version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawEdge {
    pub from: String,
    pub to: String,
    pub edge_kind: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinaryRow {
    pub name: String,
    pub root_purl: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VulnRow {
    pub vuln_id: String,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VexStatement {
    pub statement_id: String,
    pub product_purl: String,
    pub vuln_id: String,
    pub status: String,
    pub updated_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub expires_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub justification: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagePackage {
    pub norm_purl: String,
    pub canonical_raw: String,
    pub name: String,
    pub version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StageEdge {
    pub from: String,
    pub to: String,
    pub edge_kind: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StageVex {
    pub statement_id: String,
    pub product_purl: String,
    pub vuln_id: String,
    pub status: String,
    pub updated_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub expires_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AtlasStage {
    pub bundle_id: String,
    pub fingerprint: String,
    pub ingest_seq: u64,
    pub staging_digest: String,
    pub packages: Vec<StagePackage>,
    pub edges: Vec<StageEdge>,
    pub vex: Vec<StageVex>,
    pub binaries: Vec<BinaryRow>,
    pub vulnerabilities: Vec<VulnRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaiverEvidence {
    pub statement_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub expires_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImpactRow {
    pub binary: String,
    pub package_purl: String,
    pub vuln_id: String,
    pub effective_status: String,
    pub reachable: bool,
    pub waiver: Option<WaiverEvidence>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImpactAtlas {
    pub bundle_id: String,
    pub export_digest: String,
    pub impacts: Vec<ImpactRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunSeqState {
    pub run_seq: u64,
    pub last_fingerprint: String,
}

pub const STATUS_NOT_AFFECTED: &str = "not_affected";
pub const STATUS_FIXED: &str = "fixed";
pub const STATUS_UNDER: &str = "under_investigation";
pub const STATUS_AFFECTED: &str = "affected";
pub const STATUS_UNKNOWN: &str = "unknown";

pub const EDGE_RUNTIME: &str = "runtime";
