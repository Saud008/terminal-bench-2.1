use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Config {
    pub yard_cache_path: String,
    pub loto_ticket_path: String,
    pub output_root: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BusRow {
    pub bus_id: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BreakerRow {
    pub breaker_id: String,
    pub from_bus: String,
    pub to_bus: String,
    pub initial_state: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct LockoutRow {
    pub tag_id: String,
    pub equipment_ids: Vec<String>,
    pub active: bool,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ProcedureStep {
    pub step_index: u32,
    pub action: String,
    pub breaker_id: String,
    #[serde(default)]
    pub requires_isolation: bool,
    #[serde(default)]
    pub parallel_path_guard: bool,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ScenarioFile {
    pub scenario_id: String,
    pub buses: Vec<BusRow>,
    pub energized_sources: Vec<String>,
    pub breakers: Vec<BreakerRow>,
    pub lockouts: Vec<LockoutRow>,
    pub procedure: Vec<ProcedureStep>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct YardSnapshot {
    pub load_seq: u64,
    pub seed: String,
    pub scenario: String,
    pub buses: Vec<String>,
    pub breakers: Vec<BreakerRow>,
    pub energized_sources: Vec<String>,
    pub adjacency: Vec<[String; 2]>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct LotoTicket {
    pub ticket_id: String,
    pub seed: String,
    pub scenario: String,
    pub load_seq: u64,
    pub active: bool,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct StepResult {
    pub step_index: u32,
    pub action: String,
    pub breaker_id: String,
    pub safe: bool,
    pub reason_codes: Vec<String>,
    pub energized_buses: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct VerifySummary {
    pub total_steps: u32,
    pub unsafe_count: u32,
    pub final_energized_buses: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct VerifyReport {
    pub seed: String,
    pub scenario: String,
    pub loto_ticket_id: String,
    pub steps: Vec<StepResult>,
    pub summary: VerifySummary,
    pub audit_digest: String,
}

pub type BreakerStates = BTreeMap<String, String>;
