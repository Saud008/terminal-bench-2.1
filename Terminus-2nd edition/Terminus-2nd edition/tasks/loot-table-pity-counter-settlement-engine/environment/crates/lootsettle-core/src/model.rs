use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SeasonConfig {
    pub season_id: String,
    pub pool_epoch: u64,
    pub hmac_secret: String,
    pub carry_ratio: f64,
    pub pity_threshold: serde_json::Value,
    pub drop_weights: serde_json::Value,
    pub duplicate_shards: std::collections::BTreeMap<String, u64>,
    pub pity_boost_per_miss: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PullEvent {
    pub event_id: String,
    pub player_id: String,
    pub season_id: String,
    pub pool_epoch: u64,
    pub event_type: String,
    pub item_id: String,
    pub rarity: String,
    pub seq: u64,
    pub timestamp_ms: u64,
    pub nonce: String,
    pub signature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StagingSnapshot {
    pub events: Vec<PullEvent>,
    pub events_digest: String,
    pub season_id: String,
    pub pool_epoch: u64,
    pub staging_generation: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PlayerLedger {
    pub season_id: String,
    pub inventory: Vec<String>,
    pub shards: u64,
    pub pity_legendary: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PityLedgerFile {
    pub players: std::collections::BTreeMap<String, PlayerLedger>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProcessedEventsFile {
    pub event_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GenerationFile {
    pub generation: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AuditEntry {
    pub action: String,
    pub event_id: String,
    pub player_id: String,
    pub season_id: String,
    pub item_id: String,
    pub rarity: String,
    pub seq: u64,
    pub timestamp_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub shard_delta: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SettlementReport {
    pub audit_log: Vec<AuditEntry>,
    pub events_digest: String,
    pub generation: u64,
    pub layout_version: u64,
    pub players: std::collections::BTreeMap<String, PlayerLedger>,
    pub pool_epoch: u64,
    pub season_id: String,
    pub settlement_digest: String,
    pub staging_generation: u64,
}
