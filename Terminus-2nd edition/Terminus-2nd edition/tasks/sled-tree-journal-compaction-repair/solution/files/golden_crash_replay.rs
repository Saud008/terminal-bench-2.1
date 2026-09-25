use crate::btree::insert;
use crate::commit::state::{load_committed, save_committed};
use crate::journal::split_log::SplitJournalEntry;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;

const APPLIED_PATH: &str = "/app/state/applied_splits.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AppliedSplits {
    pub split_seq: BTreeSet<u64>,
}

pub fn load_applied() -> Result<AppliedSplits, String> {
    if !Path::new(APPLIED_PATH).exists() {
        return Ok(AppliedSplits::default());
    }
    let raw = fs::read_to_string(APPLIED_PATH).map_err(|e| format!("read applied: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse applied: {e}"))
}

pub fn save_applied(state: &AppliedSplits) -> Result<(), String> {
    if let Some(parent) = Path::new(APPLIED_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir applied: {e}"))?;
    }
    fs::write(APPLIED_PATH, serde_json::to_string_pretty(state).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write applied: {e}"))?;
    Ok(())
}

pub fn replay_crash_journal(table: &str, journal_path: &Path) -> Result<u32, String> {
    let file = fs::File::open(journal_path).map_err(|e| format!("open crash journal: {e}"))?;
    let reader = BufReader::new(file);
    let mut committed = load_committed()?;
    let mut tree = committed
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let mut applied_state = load_applied()?;
    let mut applied = 0u32;

    for line in reader.lines() {
        let line = line.map_err(|e| format!("read line: {e}"))?;
        if line.trim().is_empty() {
            continue;
        }
        let entry: SplitJournalEntry =
            serde_json::from_str(&line).map_err(|e| format!("parse entry: {e}"))?;
        match entry {
            SplitJournalEntry::ParentPivot { split_seq, pivot, .. } => {
                if applied_state.split_seq.contains(&split_seq) {
                    continue;
                }
                insert(&mut tree, pivot, "split-marker".into())?;
                applied_state.split_seq.insert(split_seq);
                applied += 1;
            }
            SplitJournalEntry::RightPage { split_seq, body, .. } => {
                if applied_state.split_seq.contains(&split_seq) {
                    continue;
                }
                if body.contains("duplicate") {
                    insert(&mut tree, format!("dup-{split_seq}"), body)?;
                    applied_state.split_seq.insert(split_seq);
                    applied += 1;
                }
            }
        }
    }
    save_applied(&applied_state)?;
    committed.tables.tables.insert(table.to_string(), tree);
    save_committed(&committed)?;
    Ok(applied)
}
