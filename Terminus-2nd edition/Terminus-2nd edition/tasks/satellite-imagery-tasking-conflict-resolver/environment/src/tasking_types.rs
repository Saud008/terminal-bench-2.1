use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SensorProfile {
    pub sensor_id: String,
    pub default_mode: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct PassWindow {
    pub pass_id: String,
    pub orbit_id: String,
    pub start_sec: u64,
    pub end_sec: u64,
    pub cells: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ImagingRequest {
    pub request_id: String,
    pub cell_id: String,
    pub mode: String,
    pub priority_tier: u32,
    pub contract_id: String,
    pub imaging_duration_sec: u64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SensorModeSpec {
    pub cold_setup_sec: u64,
    pub warm_setup_sec: u64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CloudForecast {
    pub pass_id: String,
    pub cell_id: String,
    pub risk_score: f64,
    #[serde(default = "default_coverage")]
    pub coverage_factor: f64,
}

fn default_coverage() -> f64 {
    1.0
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct PriorityContract {
    pub contract_id: String,
    pub preempt_rank: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ScenarioBundle {
    pub scenario_id: String,
    pub constellation_id: String,
    pub sensor_profile: SensorProfile,
    pub pass_windows: Vec<PassWindow>,
    pub imaging_requests: Vec<ImagingRequest>,
    pub sensor_modes: std::collections::BTreeMap<String, SensorModeSpec>,
    pub cloud_forecasts: Vec<CloudForecast>,
    pub priority_contracts: Vec<PriorityContract>,
}

#[derive(Debug, Clone, Serialize)]
pub struct SlotAssignment {
    pub request_id: String,
    pub pass_id: String,
    pub orbit_id: String,
    pub cell_id: String,
    pub mode: String,
    pub setup_sec: u64,
    pub effective_start_sec: u64,
    pub effective_end_sec: u64,
    pub cloud_composite: f64,
    pub preempt_rank: u32,
}

#[derive(Debug, Clone, Serialize)]
pub struct PreemptionEvent {
    pub displaced_request_id: String,
    pub winner_request_id: String,
    pub pass_id: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct TaskPlanManifest {
    pub run_token: String,
    pub scenario_id: String,
    pub constellation_id: String,
    pub assignment_count: u32,
    pub preemption_count: u32,
    pub assignments: Vec<SlotAssignment>,
    pub preemption_trace: Vec<PreemptionEvent>,
    pub mean_cloud_risk: f64,
    pub plan_digest: String,
}
