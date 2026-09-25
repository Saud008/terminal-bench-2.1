use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

const WAL_PATH: &str = "/app/state/wal-record.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WalRecord {
    pub index: String,
    pub live_doc_count: u32,
    pub wal_fsynced: bool,
    pub commit_lock_released: bool,
    pub lock_released_before_fsync: bool,
}

pub fn load_wal_record() -> Result<WalRecord, String> {
    if !Path::new(WAL_PATH).exists() {
        return Ok(WalRecord::default());
    }
    let raw = fs::read_to_string(WAL_PATH).map_err(|e| format!("read wal: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse wal: {e}"))
}

fn write_wal_record(record: &WalRecord) -> Result<(), String> {
    if let Some(parent) = Path::new(WAL_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir wal: {e}"))?;
    }
    fs::write(
        WAL_PATH,
        serde_json::to_string_pretty(record).map_err(|e| e.to_string())?,
    )
    .map_err(|e| format!("write wal: {e}"))?;
    Ok(())
}

fn wal_marker_path(index: &str) -> String {
    let safe = index.replace('/', "_");
    format!("/app/state/wal-{safe}.marker")
}

fn fsync_wal_marker(index: &str, live_docs: u32) -> Result<(), String> {
    let marker = wal_marker_path(index);
    if let Some(parent) = Path::new(&marker).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir wal marker dir: {e}"))?;
    }
    fs::write(&marker, live_docs.to_string()).map_err(|e| format!("write wal marker: {e}"))?;
    Ok(())
}

pub fn run_wal_barrier(index: &str, live_docs: u32) -> Result<(), String> {
    write_wal_record(&WalRecord {
        index: index.to_string(),
        live_doc_count: live_docs,
        wal_fsynced: false,
        commit_lock_released: true,
        lock_released_before_fsync: true,
    })?;
    fsync_wal_marker(index, live_docs)?;
    write_wal_record(&WalRecord {
        index: index.to_string(),
        live_doc_count: live_docs,
        wal_fsynced: true,
        commit_lock_released: false,
        lock_released_before_fsync: true,
    })?;
    Ok(())
}
