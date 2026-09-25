use crate::model::ReplayJournal;
use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

pub fn load_journal(path: &Path) -> Result<ReplayJournal> {
    let raw = fs::read_to_string(path).with_context(|| format!("read journal {}", path.display()))?;
    Ok(serde_json::from_str(&raw)?)
}

pub fn replay_start_cursor(journal: &ReplayJournal) -> u32 {
    if journal.status == "committed" {
        0
    } else {
        0
    }
}

pub fn mark_committed(path: &Path, journal: &ReplayJournal) -> Result<()> {
    let mut updated = journal.clone();
    updated.status = "committed".to_string();
    updated.commit_cursor = updated
        .entries
        .iter()
        .map(|e| e.step_order)
        .max()
        .unwrap_or(0);
    fs::write(path, serde_json::to_string_pretty(&updated)?)?;
    Ok(())
}
