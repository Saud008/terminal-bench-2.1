use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransferEvent {
    pub event_id: String,
    pub evidence_id: String,
    pub from_officer_id: String,
    pub to_officer_id: String,
    pub from_location_id: String,
    pub to_location_id: String,
    pub seal_number: String,
    pub expected_seal: String,
    pub event_epoch_ms: u64,
    pub event_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExhibitAlias {
    pub court_alias: String,
    pub evidence_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaseBundle {
    pub case_id: String,
    pub bundle_id: String,
    pub transfers: Vec<TransferEvent>,
    pub seal_checks: Vec<TransferEvent>,
    pub exhibit_aliases: Vec<ExhibitAlias>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub bundle_root: String,
    pub location_catalog: String,
    pub default_policy: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VaultLedger {
    pub case_id: String,
    pub bundle_id: String,
    pub run_seq: u64,
    pub transfers: Vec<TransferEvent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegisterLedger {
    pub case_id: String,
    pub bundle_id: String,
    pub ledger_seq: u64,
    pub exhibit_aliases: Vec<ExhibitAlias>,
    pub transfers: Vec<TransferEvent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LineageEdge {
    pub evidence_id: String,
    pub from_officer_id: String,
    pub to_officer_id: String,
    pub event_epoch_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntegrityFinding {
    pub evidence_id: String,
    pub code: String,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DossierSummary {
    pub intact_items: u64,
    pub defect_items: u64,
    pub seal_breaks: u64,
    pub location_invalid: u64,
    pub chronology_violation: u64,
    pub lineage_gap: u64,
    pub alias_collision: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DossierReport {
    pub case_id: String,
    pub bundle_id: String,
    pub run_seq: u64,
    pub evidence_items: Vec<String>,
    pub lineage_edges: Vec<LineageEdge>,
    pub integrity_findings: Vec<IntegrityFinding>,
    pub summary: DossierSummary,
    pub custody_digest: String,
}
