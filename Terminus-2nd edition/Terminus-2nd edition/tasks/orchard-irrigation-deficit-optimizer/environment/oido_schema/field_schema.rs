use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProbeSpec {
    pub probe_id: String,
    pub raw_vwc: f64,
    pub offset: f64,
    pub weight: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FieldSpec {
    pub area_ha: f64,
    pub crop_stage: u32,
    pub root_depth_cm: f64,
    pub probes: Vec<ProbeSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PumpSpec {
    pub max_liters_per_hour: f64,
    pub hours_per_slot: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuotaWindow {
    pub window_index: u32,
    pub max_m3: f64,
    pub max_carry_m3: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchardMeta {
    pub orchard: String,
    pub slot_hours: u32,
    pub window_count: u32,
    pub target_vwc: f64,
    pub fields: BTreeMap<String, FieldSpec>,
    pub kc_stages: Vec<f64>,
    pub et_forecast_mm: Vec<f64>,
    pub pump: PumpSpec,
    pub quota_windows: Vec<QuotaWindow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FieldLedgerRow {
    pub field_id: String,
    pub calibrated_vwc: f64,
    pub et_demand_mm: Vec<f64>,
    pub deficit_mm: Vec<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoistureLedger {
    pub run_id: String,
    pub orchard: String,
    pub window_count: u32,
    pub target_vwc: f64,
    pub fields: Vec<FieldLedgerRow>,
    pub pump: PumpSpec,
    pub quota_windows: Vec<QuotaWindow>,
    pub ledger_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IrrigationRow {
    pub field_id: String,
    pub window_index: u32,
    pub liters_applied: f64,
    pub deficit_after_mm: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuotaLedgerRow {
    pub window_index: u32,
    pub base_m3: f64,
    pub carry_in_m3: f64,
    pub used_m3: f64,
    pub carry_out_m3: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeficitTrace {
    pub field_id: String,
    pub window_index: u32,
    pub deficit_before_mm: f64,
    pub deficit_after_mm: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IrrigationPlan {
    pub run_id: String,
    pub assignments: Vec<IrrigationRow>,
    pub quota_ledger: Vec<QuotaLedgerRow>,
    pub deficit_trace: Vec<DeficitTrace>,
    pub summary: BTreeMap<String, serde_json::Value>,
    pub plan_digest: String,
}
