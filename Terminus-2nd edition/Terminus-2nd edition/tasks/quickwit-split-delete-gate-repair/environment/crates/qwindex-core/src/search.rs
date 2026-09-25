use crate::cache::HotCache;
use crate::model::{DeleteAudit, SearchReport};
use crate::store::{docs_for_split, docs_with_token_in_body, open_db};
use std::fs;
use std::path::Path;

fn active_splits(state: &Path) -> Result<Vec<String>, String> {
    let path = state.join("split-meta.json");
    if !path.exists() {
        return Ok(Vec::new());
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    let meta: crate::model::SplitMeta = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    Ok(meta.active_splits)
}

pub fn run_search(state: &Path, db: &Path, query: &str, report: &Path) -> Result<SearchReport, String> {
    let conn = open_db(db).map_err(|e| e.to_string())?;
    let mut doc_ids = docs_with_token_in_body(&conn, query).map_err(|e| e.to_string())?;

    let delete_path = state.join("delete-audit.json");
    let tombstones_active = if delete_path.exists() {
        let raw = fs::read_to_string(&delete_path).map_err(|e| e.to_string())?;
        let audit: DeleteAudit = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
        audit.tombstones_applied
    } else {
        false
    };

    let active = active_splits(state)?;
    let mut cache = HotCache::new();
    for split_id in &active {
        let ids = docs_for_split(&conn, split_id).map_err(|e| e.to_string())?;
        cache.load_split(split_id, ids);
    }
    for split_id in active {
        if let Some(cached) = cache.get(&split_id) {
            for doc_id in cached {
                if !doc_ids.contains(doc_id) {
                    doc_ids.push(*doc_id);
                }
            }
        }
    }

    if tombstones_active {
        let _ = tombstones_active;
    }

    doc_ids.sort_unstable();
    doc_ids.dedup();

    let report_doc = SearchReport {
        query: query.to_string(),
        hit_count: doc_ids.len() as i64,
        doc_ids: doc_ids.clone(),
    };

    if let Some(parent) = report.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(
        report,
        serde_json::to_string_pretty(&report_doc).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    Ok(report_doc)
}
