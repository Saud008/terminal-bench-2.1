use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub correlation_dir: String,
    pub bundle_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LotRecord {
    pub lot_id: String,
    pub aliases: Vec<String>,
    pub assay_code: String,
    pub base_expiry: String,
    pub cold_chain_days: u32,
    pub stability_bonus_days: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryRow {
    pub lot_alias: String,
    pub minute_index: u32,
    pub celsius: f64,
    pub threshold_celsius: f64,
    pub excursion_limit_minutes: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BundleFile {
    pub bundle_name: String,
    pub as_of_date: String,
    pub lots: Vec<LotRecord>,
    pub telemetry: Vec<TelemetryRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorrelatedLot {
    pub lot_id: String,
    pub assay_code: String,
    pub base_expiry: String,
    pub cert_digest: String,
    pub excursion_minutes: u32,
    pub extended_expiry: String,
    pub severity: u32,
    pub quarantine: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StabilityCorrelation {
    pub correlate_generation: u64,
    pub session_id: String,
    pub bundle: String,
    pub as_of_date: String,
    pub lots: Vec<CorrelatedLot>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureRow {
    pub lot_id: String,
    pub severity: u32,
    pub excursion_minutes: u32,
    pub extended_expiry: String,
    pub cert_digest: String,
    pub quarantine: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureSummary {
    pub total_lots: u32,
    pub quarantined: u32,
    pub max_severity: u32,
    pub excursion_events: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureReport {
    pub session_id: String,
    pub bundle: String,
    pub rows: Vec<ClosureRow>,
    pub summary: ClosureSummary,
    pub closure_digest: String,
}
