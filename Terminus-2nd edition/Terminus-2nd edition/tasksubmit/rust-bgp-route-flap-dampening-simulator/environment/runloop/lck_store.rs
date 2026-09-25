use crate::route_model::{PeerDampening, ScenarioLock};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

use crate::LOCK_PATH;

pub fn build_lock(
    scenario_id: &str,
    feed_relpath: &str,
    raw: &[u8],
    line_count: usize,
    peer_table: std::collections::BTreeMap<String, PeerDampening>,
) -> ScenarioLock {
    ScenarioLock {
        scenario_id: scenario_id.to_string(),
        feed_fingerprint: fingerprint(raw),
        feed_relpath: feed_relpath.to_string(),
        line_count: line_count as u64,
        peer_table,
    }
}

pub fn persist(lock: &ScenarioLock) -> Result<(), String> {
    let dir = Path::new(LOCK_PATH).parent().unwrap();
    fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    fs::write(
        LOCK_PATH,
        serde_json::to_string_pretty(lock).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}

pub fn load() -> Result<ScenarioLock, String> {
    let text = fs::read_to_string(LOCK_PATH).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn fingerprint(raw: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(raw);
    hex::encode(h.finalize())
}
