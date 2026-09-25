use crate::model::Checkpoint;
use std::fs;
use std::path::{Path, PathBuf};

pub fn checkpoint_path(state: &Path) -> PathBuf {
    state.join("checkpoint.json")
}

pub fn load_checkpoint(state: &Path) -> Result<Checkpoint, String> {
    let path = checkpoint_path(state);
    if !path.exists() {
        return Ok(Checkpoint {
            merge_seq: 0,
            last_complete_merge: 0,
        });
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_checkpoint(state: &Path, cp: &Checkpoint) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(cp).map_err(|e| e.to_string())?;
    fs::write(checkpoint_path(state), raw).map_err(|e| e.to_string())
}

pub fn record_merge_attempt(state: &Path, complete: bool) -> Result<(), String> {
    let mut cp = load_checkpoint(state)?;
    cp.merge_seq += 1;
    if complete {
        cp.last_complete_merge += 1;
    }
    save_checkpoint(state, &cp)
}
