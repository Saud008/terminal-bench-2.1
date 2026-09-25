use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Config {
    pub ledger_dir: String,
    pub authorized_roles: Vec<String>,
    pub denylist: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ShiftBundle {
    pub plant_id: String,
    pub shift: String,
    pub as_of: String,
    pub target_turbidity_ntu: f64,
    pub min_flow_lpm: f64,
    pub minute_dose_cap_mg: f64,
    pub chemicals: Vec<ChemicalLot>,
    pub flow_readings: Vec<FlowReading>,
    pub turbidity_readings: Vec<TurbidityReading>,
    pub overrides: Vec<OverrideRecord>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ChemicalLot {
    pub chem_id: String,
    pub lot_code: String,
    pub unit: String,
    pub concentration: f64,
    pub max_dose_mg: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct FlowReading {
    pub sensor_id: String,
    pub minute: u32,
    pub m3_h: f64,
    pub status: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct TurbidityReading {
    pub sensor_id: String,
    pub minute: u32,
    pub ntu: f64,
    pub status: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct OverrideRecord {
    pub user: String,
    pub role: String,
    pub chem_id: String,
    pub factor: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ChemicalDoseRow {
    pub chem_id: String,
    pub arc_tok: String,
    pub weighted_conc_mg_l: f64,
    pub total_dose_mg: f64,
    pub max_dose_mg: f64,
    pub contact_excluded_minutes: u32,
    pub override_applied: bool,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DoseLedger {
    pub ledger_revision_token: String,
    pub plant_id: String,
    pub shift: String,
    pub as_of: String,
    pub chemicals: Vec<ChemicalDoseRow>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BreachRow {
    pub chem_id: String,
    pub total_dose_mg: f64,
    pub max_dose_mg: f64,
    pub severity_pct: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SafetySummary {
    pub plant_id: String,
    pub shift: String,
    pub chemical_count: u32,
    pub breach_count: u32,
    pub max_severity_pct: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SafetyReport {
    pub plant_id: String,
    pub shift: String,
    pub rows: Vec<BreachRow>,
    pub summary: SafetySummary,
    pub breach_atlas_seal: String,
}