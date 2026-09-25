use std::fs;
use std::path::Path;

use sha2::{Digest, Sha256};
use serde_json::Value;

use crate::types::StageSnapshot;
use crate::DEFAULT_STAGE_PATH;

pub fn write_stage(snap: &StageSnapshot) -> Result<(), String> {
    let path = Path::new(DEFAULT_STAGE_PATH);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(snap).map_err(|e| e.to_string())?;
    fs::write(path, text).map_err(|e| e.to_string())
}

pub fn read_stage() -> Result<StageSnapshot, String> {
    let text = fs::read_to_string(DEFAULT_STAGE_PATH).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

pub fn stage_digest(snap: &StageSnapshot) -> Result<String, String> {
    let mut clone = snap.clone();
    clone.merged_counters = None;
    clone.merge_generation = 0;
    let val = serde_json::to_value(&clone).map_err(|e| e.to_string())?;
    let sorted = sort_json(val);
    let canon = serde_json::to_string(&sorted).map_err(|e| e.to_string())?;
    Ok(hex::encode(Sha256::digest(canon.as_bytes())))
}

fn sort_json(value: Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().cloned().collect();
            keys.sort();
            let mut out = serde_json::Map::new();
            for k in keys {
                if let Some(v) = map.get(&k) {
                    out.insert(k, sort_json(v.clone()));
                }
            }
            Value::Object(out)
        }
        Value::Array(arr) => Value::Array(arr.into_iter().map(sort_json).collect()),
        other => other,
    }
}
