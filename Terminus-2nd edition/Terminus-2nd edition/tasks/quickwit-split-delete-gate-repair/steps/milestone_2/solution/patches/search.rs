use crate::model::{DeleteAudit, SearchReport};
use crate::store::{docs_with_token_in_body, is_tombstoned, open_db};
use std::fs;
use std::path::Path;

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

    if tombstones_active {
        doc_ids.retain(|doc_id| {
            !is_tombstoned(&conn, *doc_id).unwrap_or(false)
        });
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
