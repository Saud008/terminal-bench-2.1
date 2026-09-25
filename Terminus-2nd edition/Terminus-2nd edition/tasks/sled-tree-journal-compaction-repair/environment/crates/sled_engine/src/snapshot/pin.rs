use crate::commit::state::load_committed;
use crate::page::registry::load_registry;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PinSet {
    pub table: String,
    pub snapshot_id: String,
    pub pinned_pages: BTreeSet<String>,
}

fn pin_path(table: &str, snapshot_id: &str) -> PathBuf {
    PathBuf::from(format!("/app/state/pins/{table}-{snapshot_id}.json"))
}

pub fn pin_snapshot(table: &str, snapshot_id: &str) -> Result<(), String> {
    let committed = load_committed()?;
    let tree = committed
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let reg = load_registry()?;
    let mut pinned = BTreeSet::new();
    for page_id in reg.pages.keys() {
        if page_id.starts_with("root") {
            pinned.insert(page_id.clone());
        }
    }
    let _tree = tree;
    let pin = PinSet {
        table: table.to_string(),
        snapshot_id: snapshot_id.to_string(),
        pinned_pages: pinned,
    };
    let path = pin_path(table, snapshot_id);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir pins: {e}"))?;
    }
    fs::write(path, serde_json::to_string_pretty(&pin).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write pin: {e}"))?;
    Ok(())
}

pub fn load_pin_set(table: &str) -> Result<BTreeSet<String>, String> {
    let dir = PathBuf::from("/app/state/pins");
    if !dir.is_dir() {
        return Ok(BTreeSet::new());
    }
    let mut out = BTreeSet::new();
    for entry in fs::read_dir(&dir).map_err(|e| format!("read pins dir: {e}"))? {
        let entry = entry.map_err(|e| format!("dir entry: {e}"))?;
        let name = entry.file_name().to_string_lossy().to_string();
        if !name.starts_with(&format!("{table}-")) {
            continue;
        }
        let raw = fs::read_to_string(entry.path()).map_err(|e| format!("read pin file: {e}"))?;
        let pin: PinSet = serde_json::from_str(&raw).map_err(|e| format!("parse pin: {e}"))?;
        out.extend(pin.pinned_pages);
    }
    Ok(out)
}
