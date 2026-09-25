use std::fs;
use std::path::Path;

use sha2::{Digest, Sha256};

use crate::model::{MigrateExport, MigrateSnapshot, WorldSpec};

pub const DEFAULT_PATH: &str = "/app/state/archectl-replay-ledger.json";

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ReplayLedger {
    pub ledger_version: u32,
    pub seed: String,
    pub journal_op_count: u32,
    pub generation_digest: String,
    pub sealed: bool,
}

pub fn validate_replay(doc: &MigrateExport, spec: &WorldSpec, seed: &str) -> Result<(), String> {
    if doc.seed != seed {
        return Err("replay seed mismatch".into());
    }
    if doc.generation == 0 && (!spec.entities.is_empty() || !spec.journal.is_empty()) {
        return Err("replay generation unset".into());
    }
    Ok(())
}

pub fn generation_digest(doc: &MigrateExport) -> String {
    let mut entities = doc.entities.clone();
    entities.sort_by_key(|row| row.id);
    let entity_ids: Vec<_> = entities.iter().map(|row| row.id).collect();

    let mut raw = String::new();
    use std::fmt::Write as _;
    raw.push('{');
    write!(raw, "\"seed\":{}", serde_json::to_string(&doc.seed).expect("seed json")).expect("seed");
    write!(raw, ",\"generation\":{}", doc.generation).expect("generation");
    write!(raw, ",\"component_map\":{{").expect("component_map");
    for (idx, (name, id)) in doc.component_map.iter().enumerate() {
        if idx > 0 {
            raw.push(',');
        }
        write!(raw, "\"{name}\":{id}").expect("component");
    }
    write!(raw, "}},\"entity_ids\":[").expect("entity_ids");
    for (idx, eid) in entity_ids.iter().enumerate() {
        if idx > 0 {
            raw.push(',');
        }
        write!(raw, "{eid}").expect("entity id");
    }
    raw.push_str("]}");
    format!("{:x}", Sha256::digest(raw.as_bytes()))
}

pub fn write(path: &str, spec: &WorldSpec, seed: &str, doc: &MigrateExport) -> Result<(), String> {
    let ledger = ReplayLedger {
        ledger_version: 1,
        seed: seed.to_string(),
        journal_op_count: spec.journal.len() as u32,
        generation_digest: generation_digest(doc),
        sealed: true,
    };
    write_json(path, &ledger)
}

pub fn load(path: &str) -> Result<ReplayLedger, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn assert_migrate_ready(
    ledger: &ReplayLedger,
    spec: &WorldSpec,
    seed: &str,
    snap: &MigrateSnapshot,
) -> Result<(), String> {
    if !ledger.sealed {
        return Err("replay ledger is not sealed".into());
    }
    if ledger.seed != seed {
        return Err("replay ledger seed mismatch".into());
    }
    if ledger.journal_op_count as usize != spec.journal.len() {
        return Err("replay ledger journal op count mismatch".into());
    }
    let export = MigrateExport::from(snap.clone());
    if ledger.generation_digest != generation_digest(&export) {
        return Err("replay ledger generation digest mismatch".into());
    }
    Ok(())
}

fn write_json<T: serde::Serialize>(path: &str, value: &T) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let raw = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    fs::write(path, format!("{raw}\n")).map_err(|e| e.to_string())
}
