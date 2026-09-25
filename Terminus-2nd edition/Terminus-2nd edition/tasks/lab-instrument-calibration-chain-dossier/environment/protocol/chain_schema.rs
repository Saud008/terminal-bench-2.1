use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Config {
    pub vault_path: String,
    pub register_path: String,
    pub coverage_factor: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ReadingRow {
    pub channel: String,
    pub value: f64,
    pub unit: String,
    pub nominal: f64,
    pub tol_plus: f64,
    pub tol_minus: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Certificate {
    pub cert_id: String,
    pub issued: String,
    pub expires: String,
    pub issuer: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct StandardLink {
    pub std_id: String,
    pub parent_std: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Technician {
    pub tech_id: String,
    pub scope_instruments: Vec<String>,
    pub qual_expires: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct UncertaintyComponent {
    pub component: String,
    pub value: f64,
    pub degrees_freedom: i32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct RunPack {
    pub run_id: String,
    pub as_of_date: String,
    pub instrument_id: String,
    pub readings: Vec<ReadingRow>,
    pub certificate: Certificate,
    pub standard_chain: Vec<StandardLink>,
    pub technician: Technician,
    pub uncertainty_budget: Vec<UncertaintyComponent>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ChannelDecision {
    pub channel: String,
    pub within_tolerance: bool,
    pub deviation: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct StagedInstrument {
    pub instrument_id: String,
    pub cert_valid: bool,
    pub cert_digest: String,
    pub std_root: String,
    pub combined_uncertainty: f64,
    pub expanded_uncertainty: f64,
    pub authorized_tech: bool,
    pub decisions: Vec<ChannelDecision>,
    pub out_of_tolerance_count: i32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct VaultSnapshot {
    pub batch_id: String,
    pub pack: String,
    pub as_of_date: String,
    pub instrument: StagedInstrument,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DossierRow {
    pub instrument_id: String,
    pub severity: i32,
    pub out_of_tolerance_count: i32,
    pub cert_valid: bool,
    pub authorized_tech: bool,
    pub expanded_uncertainty: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DossierSummary {
    pub instrument_count: i32,
    pub invalid_cert_count: i32,
    pub unauthorized_tech_count: i32,
    pub oot_channel_total: i32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DossierReport {
    pub batch_id: String,
    pub fuse_generation: i32,
    pub rows: Vec<DossierRow>,
    pub summary: DossierSummary,
    pub dossier_digest: String,
}
