use crate::models::SeasonPack;
use std::path::Path;

pub fn read_season_pack(path: &Path) -> Result<SeasonPack, String> {
    let raw = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn bind_path(token: &str) -> String {
    format!("{}/season-bind-{}.json", crate::VAR_ROOT, token)
}

pub fn ledger_path(token: &str) -> String {
    format!("{}/quota-ledger-{}.jsonl", crate::VAR_ROOT, token)
}

pub fn header_path(token: &str) -> String {
    format!("{}/quota-ledger-{}.header.json", crate::VAR_ROOT, token)
}
