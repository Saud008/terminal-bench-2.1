use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Config {
    pub trackgraph_cache_path: String,
    pub possession_gen_path: String,
    pub scenario_root: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ScenarioFile {
    pub scenario_id: String,
    pub blocks: Vec<BlockRow>,
    pub adjacency: Vec<[String; 2]>,
    pub possessions: Vec<PossessionClaim>,
    pub signals: Vec<SignalRestriction>,
    pub reservations: Vec<TrainReservation>,
    pub overrides: Vec<CrisisOverride>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BlockRow {
    pub block_id: String,
    pub kilometer: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct PossessionClaim {
    pub claim_id: String,
    pub blocks: Vec<String>,
    pub start_min: u64,
    pub end_min: u64,
    pub priority: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SignalRestriction {
    pub signal_id: String,
    pub block_id: String,
    pub aspect: String,
    pub start_min: u64,
    pub end_min: u64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct TrainReservation {
    pub train_id: String,
    pub blocks: Vec<String>,
    pub start_min: u64,
    pub end_min: u64,
    pub priority: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CrisisOverride {
    pub override_id: String,
    pub blocks: Vec<String>,
    pub start_min: u64,
    pub end_min: u64,
    pub priority: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct TopoCacheSnapshot {
    pub load_seq: u64,
    pub seed: String,
    pub scenario: String,
    pub blocks: Vec<String>,
    pub zone_map: std::collections::BTreeMap<String, Vec<String>>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct PossessionGeneration {
    pub seed: String,
    pub scenario: String,
    pub possession_id: String,
    pub load_seq: u64,
    pub active: bool,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ConflictRow {
    pub group_key: String,
    pub participants: Vec<String>,
    pub window_start: u64,
    pub window_end: u64,
    pub blocks: Vec<String>,
    pub reasons: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ConflictSummary {
    pub total_conflicts: u32,
    pub signal_blocked: u32,
    pub override_suppressed: u32,
    pub possession_pairs: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ConflictLedger {
    pub seed: String,
    pub scenario: String,
    pub possession_id: String,
    pub conflict_groups: Vec<ConflictRow>,
    pub summary: ConflictSummary,
    pub audit_digest: String,
}
