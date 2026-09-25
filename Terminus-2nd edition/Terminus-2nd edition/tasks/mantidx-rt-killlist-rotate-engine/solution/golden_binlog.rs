use crate::model::BinlogCheckpoint;
use crate::store::{commit_all_pending, max_binlog_seq, open_db};
use std::fs;
use std::path::{Path, PathBuf};

pub fn checkpoint_path(state: &Path) -> PathBuf {
    state.join("binlog-checkpoint.json")
}

pub fn load_checkpoint(state: &Path) -> Result<BinlogCheckpoint, String> {
    let path = checkpoint_path(state);
    if !path.exists() {
        return Ok(BinlogCheckpoint {
            last_committed_seq: 0,
            rotate_seq: 0,
        });
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_checkpoint(state: &Path, cp: &BinlogCheckpoint) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(cp).map_err(|e| e.to_string())?;
    fs::write(checkpoint_path(state), raw).map_err(|e| e.to_string())
}

pub fn checkpoint_after_rotate(state: &Path, db: &Path, rotate_seq: i64) -> Result<i64, String> {
    let conn = open_db(db).map_err(|e| e.to_string())?;
    commit_all_pending(&conn).map_err(|e| e.to_string())?;
    let seq = max_binlog_seq(&conn).map_err(|e| e.to_string())?;
    save_checkpoint(
        state,
        &BinlogCheckpoint {
            last_committed_seq: seq,
            rotate_seq,
        },
    )?;
    Ok(seq)
}
