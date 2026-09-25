use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScenarioMeta {
    pub scenario: String,
    pub slot_minutes: u32,
    pub window_count: u32,
    pub regions: BTreeMap<String, RegionSpec>,
    pub intensity: BTreeMap<String, Vec<f64>>,
    pub jobs: Vec<JobSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegionSpec {
    pub quota_per_window: u32,
    pub max_carryover: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobSpec {
    pub job_id: String,
    pub compute_units: u32,
    pub duration_slots: u32,
    pub deadline_slot: u32,
    pub allowed_regions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HarmonizedLedger {
    pub run_id: String,
    pub scenario: String,
    pub slot_minutes: u32,
    pub window_count: u32,
    pub regions: BTreeMap<String, RegionSpec>,
    pub intensity: BTreeMap<String, Vec<f64>>,
    pub jobs: Vec<JobSpec>,
    pub normalized_windows: Vec<WindowSlot>,
    pub harmonized_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowSlot {
    pub index: u32,
    pub start_minute: u32,
    pub end_minute: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssignmentRow {
    pub job_id: String,
    pub region: String,
    pub start_slot: u32,
    pub carbon_mass_g: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuotaLedgerRow {
    pub region: String,
    pub window_index: u32,
    pub base_quota: u32,
    pub carry_in: u32,
    pub used: u32,
    pub carry_out: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InfeasRow {
    pub job_id: String,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShiftAtlas {
    pub run_id: String,
    pub assignments: Vec<AssignmentRow>,
    pub quota_ledger: Vec<QuotaLedgerRow>,
    pub blocked_jobs: Vec<InfeasRow>,
    pub summary: BTreeMap<String, serde_json::Value>,
    pub plan_digest: String,
}
