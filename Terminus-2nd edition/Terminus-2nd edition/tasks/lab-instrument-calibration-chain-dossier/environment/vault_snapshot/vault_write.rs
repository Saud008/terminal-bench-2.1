use crate::chain_schema::{StagedInstrument, VaultSnapshot};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub fn read_vault(path: &str) -> Result<HashMap<String, VaultSnapshot>, String> {
    if !Path::new(path).exists() {
        return Ok(HashMap::new());
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn write_vault(path: &str, map: &HashMap<String, VaultSnapshot>) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let body = serde_json::to_string_pretty(map).map_err(|e| e.to_string())?;
    fs::write(path, body).map_err(|e| e.to_string())
}

pub fn upsert_batch(
    path: &str,
    batch_id: &str,
    pack: &str,
    as_of_date: &str,
    instrument: StagedInstrument,
) -> Result<(), String> {
    let mut map = read_vault(path)?;
    let entry = map.entry(batch_id.to_string()).or_insert(VaultSnapshot {
        batch_id: batch_id.to_string(),
        pack: String::new(),
        as_of_date: String::new(),
        instrument: instrument.clone(),
    });
    entry.pack = pack.to_string();
    entry.as_of_date = as_of_date.to_string();
    entry.instrument = instrument;
    write_vault(path, &map)
}
