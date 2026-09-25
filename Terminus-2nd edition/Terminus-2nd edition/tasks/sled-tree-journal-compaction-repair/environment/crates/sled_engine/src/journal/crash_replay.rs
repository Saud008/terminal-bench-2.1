use crate::btree::insert;
use crate::commit::state::{load_committed, save_committed};
use crate::journal::split_log::SplitJournalEntry;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;

const RUN_PATH: &str = "/app/state/journal_replay_run.json";

fn bump_replay_run() -> Result<u64, String> {
    let mut run = 0u64;
    if Path::new(RUN_PATH).exists() {
        let raw = fs::read_to_string(RUN_PATH).map_err(|e| format!("read replay run: {e}"))?;
        run = raw.trim().parse().unwrap_or(0);
    }
    run += 1;
    fs::write(RUN_PATH, run.to_string()).map_err(|e| format!("write replay run: {e}"))?;
    Ok(run)
}

pub fn replay_crash_journal(table: &str, journal_path: &Path) -> Result<u32, String> {
    let run = bump_replay_run()?;
    let file = fs::File::open(journal_path).map_err(|e| format!("open crash journal: {e}"))?;
    let reader = BufReader::new(file);
    let mut committed = load_committed()?;
    let mut tree = committed
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let mut applied = 0u32;

    for line in reader.lines() {
        let line = line.map_err(|e| format!("read line: {e}"))?;
        if line.trim().is_empty() {
            continue;
        }
        let entry: SplitJournalEntry =
            serde_json::from_str(&line).map_err(|e| format!("parse entry: {e}"))?;
        match entry {
            SplitJournalEntry::ParentPivot { pivot, .. } => {
                insert(
                    &mut tree,
                    format!("journal-run-{run}"),
                    format!("{pivot}:applied"),
                )?;
                applied += 1;
            }
            SplitJournalEntry::RightPage { body, .. } => {
                if body.contains("duplicate") {
                    insert(
                        &mut tree,
                        format!("journal-dup-{run}"),
                        body.clone(),
                    )?;
                    applied += 1;
                }
            }
        }
    }
    committed.tables.tables.insert(table.to_string(), tree);
    save_committed(&committed)?;
    Ok(applied)
}
