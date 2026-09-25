use crate::plant_schema::{ChemicalDoseRow, DoseLedger};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn revision_token(plant_id: &str, shift: &str, as_of: &str) -> String {
    let body = format!("{plant_id}:{shift}:{as_of}");
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())[..12].to_string()
}

pub fn write_ledger(
    path: &str,
    plant_id: &str,
    shift: &str,
    as_of: &str,
    _prev_token: &str,
    chemicals: Vec<ChemicalDoseRow>,
) -> Result<(), String> {
    let ledger = DoseLedger {
        ledger_revision_token: revision_token(plant_id, shift, as_of),
        plant_id: plant_id.to_string(),
        shift: shift.to_string(),
        as_of: as_of.to_string(),
        chemicals,
    };
    write_json(path, &ledger)
}

pub fn read_ledger(path: &str) -> Result<DoseLedger, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn read_revision_token(path: &str) -> String {
    read_ledger(path)
        .map(|l| l.ledger_revision_token)
        .unwrap_or_default()
}

fn write_json(path: &str, v: &DoseLedger) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(v).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
