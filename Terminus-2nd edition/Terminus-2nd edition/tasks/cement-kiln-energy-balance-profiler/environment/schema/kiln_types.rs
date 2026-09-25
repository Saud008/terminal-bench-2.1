use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub tele_buffer_dir: String,
    pub fuel_buffer_dir: String,
    pub probe_grid_dir: String,
    pub balance_scratch_dir: String,
    pub kcal_to_mj: f64,
    pub default_specific_heat_mj_per_t: f64,
    pub grid_step_sec: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryRow {
    pub probe_id: String,
    pub probe_ts: u64,
    pub temp_raw: f64,
    pub unit: String,
    pub cal_offset_c: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagedTelemetry {
    pub probe_id: String,
    pub probe_ts: u64,
    pub temp_norm_c: f64,
    pub cal_offset_c: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuelBatch {
    pub batch_id: String,
    pub fuel_name: String,
    pub mass_kg: f64,
    pub cv_kcal_kg: f64,
    pub start_ts: u64,
    pub end_ts: u64,
    pub energy_mj: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClinkerWindow {
    pub window_id: String,
    pub batch_id: String,
    pub clinker_t: f64,
    pub start_ts: u64,
    pub end_ts: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProbeWindow {
    pub probe_ts: u64,
    pub probe_id: String,
    pub temp_c: f64,
    pub batch_id: String,
    pub interpolated: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BalanceScratch {
    pub run_id: String,
    pub energy_in_mj: f64,
    pub clinker_out_t: f64,
    pub clinker_energy_mj: f64,
    pub heat_loss_mj: f64,
    pub residual_mj: f64,
    pub residual_mj_per_t: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeatBalanceLedger {
    pub run_id: String,
    pub kiln_id: String,
    pub energy_in_mj: f64,
    pub clinker_out_t: f64,
    pub heat_loss_mj: f64,
    pub residual_mj: f64,
    pub residual_mj_per_t: f64,
    pub fuel_batches: Vec<FuelBatch>,
    pub probe_windows: Vec<ProbeWindow>,
    pub lineage_digest: String,
    pub audit_digest: String,
}
