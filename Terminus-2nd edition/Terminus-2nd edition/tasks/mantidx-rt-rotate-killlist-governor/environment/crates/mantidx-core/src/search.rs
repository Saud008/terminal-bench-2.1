use crate::model::SearchReport;
use crate::store::{docs_matching, open_db, searchable_hits};
use std::fs;
use std::path::Path;

pub fn run_search(state: &Path, db: &Path, query: &str, report_path: &Path) -> Result<SearchReport, String> {
    let conn = open_db(db).map_err(|e| e.to_string())?;
    let mut doc_ids = searchable_hits(&conn, query).map_err(|e| e.to_string())?;

    let revived = docs_matching(&conn, query).map_err(|e| e.to_string())?;
    for (doc_id, _body, _seg, killed) in revived {
        if killed != 0 {
            if !doc_ids.contains(&doc_id) {
                doc_ids.push(doc_id);
            }
        }
    }
    doc_ids.sort_unstable();

    let report = SearchReport {
        query: query.to_string(),
        hit_count: doc_ids.len() as i64,
        doc_ids,
    };
    let raw = serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?;
    fs::write(report_path, raw).map_err(|e| e.to_string())?;
    let _ = state;
    Ok(report)
}
