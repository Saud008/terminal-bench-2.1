use crate::route_model::FlapLedger;
use std::fs;
use std::path::Path;

use crate::LEDGER_PATH;
use crate::RUN_COUNTER_PATH;

pub fn read_run_id() -> u64 {
    if let Ok(text) = fs::read_to_string(RUN_COUNTER_PATH) {
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(&text) {
            return v.get("run_id").and_then(|x| x.as_u64()).unwrap_or(0);
        }
    }
    0
}

pub fn write_ledger(ledger: &FlapLedger) -> Result<(), String> {
    let dir = Path::new(LEDGER_PATH).parent().unwrap();
    fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    fs::write(
        LEDGER_PATH,
        serde_json::to_string_pretty(ledger).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}

pub fn load_ledger() -> Result<FlapLedger, String> {
    let text = fs::read_to_string(LEDGER_PATH).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

pub fn advance_run_id(next: u64) -> Result<(), String> {
    let dir = Path::new(RUN_COUNTER_PATH).parent().unwrap();
    fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    let body = serde_json::json!({"run_id": next});
    fs::write(
        RUN_COUNTER_PATH,
        serde_json::to_string_pretty(&body).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}
