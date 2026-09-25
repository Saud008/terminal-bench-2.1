use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use ts_tokenize::token_dedupe::index_terms;
use ts_types::document::Document;
use ts_types::index::IndexFile;

use crate::parse::parse_line;
use crate::staging::write_staging;

const STAGING_PATH: &str = "/app/state/index-staging.json";

pub fn ingest_batch(index_path: &Path, batch_path: &Path) -> Result<usize, String> {
    let raw = fs::read_to_string(batch_path).map_err(|e| e.to_string())?;
    let mut index = IndexFile::load(index_path).unwrap_or_default();
    let mut parsed = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let doc = parse_line(line, index.next_order)?;
        index.next_order += 1;
        parsed.push(doc);
    }
    merge_documents(&mut index.documents, &parsed);
    rebuild_token_index(&mut index);
    IndexFile::save(index_path, &index)?;
    write_staging(Path::new(STAGING_PATH), &raw, &parsed, false)?;
    Ok(parsed.len())
}

fn merge_documents(existing: &mut Vec<Document>, incoming: &[Document]) {
    for doc in incoming {
        if let Some(slot) = existing.iter_mut().find(|d| d.docid == doc.docid) {
            let keep = slot.insertion_order;
            *slot = doc.clone();
            slot.insertion_order = keep;
        } else {
            existing.push(doc.clone());
        }
    }
}

fn rebuild_token_index(index: &mut IndexFile) {
    let mut map: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for doc in &index.documents {
        for term in index_terms(&doc.searchable_text()) {
            map.entry(term).or_default().push(doc.docid.clone());
        }
    }
    for ids in map.values_mut() {
        ids.sort();
        ids.dedup();
    }
    index.token_index = map;
}

pub fn staging_path() -> PathBuf {
    PathBuf::from(STAGING_PATH)
}
