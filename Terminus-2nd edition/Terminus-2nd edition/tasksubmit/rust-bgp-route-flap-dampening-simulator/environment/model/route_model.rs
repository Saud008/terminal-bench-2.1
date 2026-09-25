use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum FeedKind {
    Announce,
    Withdraw,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct FeedEvent {
    pub ts_ms: u64,
    pub peer: String,
    pub prefix: String,
    pub kind: FeedKind,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PeerDampening {
    pub peer_id: String,
    pub suppress_threshold: u64,
    pub reuse_threshold: u64,
    pub half_life_ms: u64,
    pub flap_penalty: u64,
    pub max_penalty: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ScenarioSpec {
    pub scenario_id: String,
    pub feed_path: String,
    pub peers: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ScenarioLock {
    pub scenario_id: String,
    pub feed_fingerprint: String,
    pub feed_relpath: String,
    pub line_count: u64,
    pub peer_table: BTreeMap<String, PeerDampening>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PrefixLedger {
    pub penalty: u64,
    pub advertised: bool,
    pub suppressed: bool,
    pub flap_count: u64,
    pub peak_penalty: u64,
    pub last_ts_ms: u64,
    pub stable_at_ms: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct FlapLedger {
    pub scenario_id: String,
    pub run_id: u64,
    pub entries: BTreeMap<String, PrefixLedger>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SuppressionLine {
    pub peer_id: String,
    pub prefix: String,
    pub final_penalty: u64,
    pub suppressed: bool,
    pub flap_count: u64,
    pub peak_penalty: u64,
    pub stable_at_ms: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReuseForecastLine {
    pub peer_id: String,
    pub prefix: String,
    pub penalty_now: u64,
    pub reuse_threshold: u64,
    pub half_life_ms: u64,
    pub ms_to_reuse: u64,
    pub forecast_anchor_ms: u64,
    pub slot_digest: String,
}

pub fn ledger_key(peer: &str, prefix: &str) -> String {
    format!("{peer}:{prefix}")
}

pub fn fallback_peer(peer_id: &str) -> PeerDampening {
    PeerDampening {
        peer_id: peer_id.to_string(),
        suppress_threshold: 2000,
        reuse_threshold: 750,
        half_life_ms: 300_000,
        flap_penalty: 1000,
        max_penalty: 16_000,
    }
}
