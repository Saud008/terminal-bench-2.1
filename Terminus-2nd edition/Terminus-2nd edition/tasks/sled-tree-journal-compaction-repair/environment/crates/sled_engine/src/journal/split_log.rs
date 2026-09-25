use crate::page::{persist_page, PageHeader};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

const JOURNAL_PATH: &str = "/app/state/split_journal.jsonl";

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "kind")]
pub enum SplitJournalEntry {
    ParentPivot {
        table: String,
        split_seq: u64,
        pivot: String,
    },
    RightPage {
        table: String,
        split_seq: u64,
        page_id: String,
        generation: u64,
        body: String,
    },
}

pub fn append_split_event(
    table: &str,
    split_seq: u64,
    page_id: &str,
    pivot: &str,
    generation: u64,
    body: String,
) -> Result<(), String> {
    persist_page(
        page_id,
        PageHeader::new(page_id, generation, None),
        body.clone(),
    )?;
    append_entry(&SplitJournalEntry::RightPage {
        table: table.to_string(),
        split_seq,
        page_id: page_id.to_string(),
        generation,
        body,
    })?;
    append_entry(&SplitJournalEntry::ParentPivot {
        table: table.to_string(),
        split_seq,
        pivot: pivot.to_string(),
    })
}

fn append_entry(entry: &SplitJournalEntry) -> Result<(), String> {
    if let Some(parent) = Path::new(JOURNAL_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir journal: {e}"))?;
    }
    let line = serde_json::to_string(entry).map_err(|e| e.to_string())?;
    use std::io::Write;
    let mut file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(JOURNAL_PATH)
        .map_err(|e| format!("open journal: {e}"))?;
    writeln!(file, "{line}").map_err(|e| format!("write journal: {e}"))?;
    Ok(())
}

pub fn record_splits_for_table(table: &str, split_count: u32) -> Result<(), String> {
    for seq in 1..=split_count {
        let page_id = format!("{table}-split-{seq}-right");
        append_split_event(
            table,
            seq as u64,
            &page_id,
            &format!("pivot-{seq}"),
            1,
            format!("right-body-{seq}"),
        )?;
    }
    Ok(())
}
