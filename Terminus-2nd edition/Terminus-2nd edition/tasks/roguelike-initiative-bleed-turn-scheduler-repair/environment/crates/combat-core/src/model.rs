use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Actor {
    pub id: String,
    pub name: String,
    pub initiative: i32,
    pub hp: i32,
    pub max_hp: i32,
    pub bleed: i32,
    pub action_points: i32,
    #[serde(default)]
    pub stunned: bool,
    #[serde(default)]
    pub pinned: bool,
    #[serde(default = "default_true")]
    pub alive: bool,
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RosterDoc {
    pub rounds: u32,
    pub actors: Vec<Actor>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagingDoc {
    pub staging_version: u32,
    pub rounds: u32,
    pub actors: Vec<Actor>,
    pub checksum: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CombatEvent {
    pub kind: String,
    pub actor: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub damage: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hp_after: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub bleed_after: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ap_after: Option<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoundLog {
    pub round: u32,
    pub events: Vec<CombatEvent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CombatState {
    pub state_version: u32,
    pub seed: String,
    pub rounds_planned: u32,
    pub actors: Vec<Actor>,
    pub rounds: Vec<RoundLog>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptExport {
    pub export_version: u32,
    pub seed: String,
    pub transcript_hash: String,
    pub rounds: Vec<RoundLog>,
    pub actors_final: Vec<Actor>,
}
