use crate::docstore::run_docstore_gc;
use crate::index::tokenize;
use crate::model::DeleteAudit;
use crate::store::{docs_with_token_in_body, open_db, tombstone_docs, clear_postings_for_docs};
use rusqlite::Connection;
use std::fs;
use std::path::Path;

pub fn load_delete_audit(state: &Path) -> Result<Option<DeleteAudit>, String> {
    let path = state.join("delete-audit.json");
    if !path.exists() {
        return Ok(None);
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    Ok(Some(
        serde_json::from_str(&raw).map_err(|e| e.to_string())?,
    ))
}

fn save_delete_audit(state: &Path, audit: &DeleteAudit) -> Result<(), String> {
    fs::write(
        state.join("delete-audit.json"),
        serde_json::to_string_pretty(audit).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}

fn purge_pending_matching(conn: &Connection, query: &str) -> Result<Vec<i64>, String> {
    let needle = query.to_lowercase();
    let mut stmt = conn
        .prepare("SELECT doc_id, body FROM pending_docs ORDER BY doc_id")
        .map_err(|e| e.to_string())?;
    let rows: Vec<(i64, String)> = stmt
        .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))
        .map_err(|e| e.to_string())?
        .collect::<Result<_, _>>()
        .map_err(|e| e.to_string())?;
    let mut removed = Vec::new();
    for (doc_id, body) in rows {
        if body
            .split_whitespace()
            .any(|token| token.to_lowercase() == needle)
        {
            conn.execute(
                "DELETE FROM pending_docs WHERE doc_id = ?1",
                rusqlite::params![doc_id],
            )
            .map_err(|e| e.to_string())?;
            removed.push(doc_id);
        }
    }
    Ok(removed)
}

/// Queue delete-by-query; tombstones are applied during split publish.
pub fn run_delete(state: &Path, db: &Path, query: &str) -> Result<DeleteAudit, String> {
    let audit = DeleteAudit {
        query: query.to_string(),
        delete_gate_open: false,
        tombstones_applied: false,
        docstore_gc_ran: false,
    };
    save_delete_audit(state, &audit)?;
    let _ = docs_with_token_in_body(&open_db(db).map_err(|e| e.to_string())?, query);
    let _ = tokenize(query);
    Ok(audit)
}

pub fn apply_pending_deletes(state: &Path, db: &Path) -> Result<DeleteAudit, String> {
    let Some(mut audit) = load_delete_audit(state)? else {
        return Ok(DeleteAudit {
            query: String::new(),
            delete_gate_open: true,
            tombstones_applied: true,
            docstore_gc_ran: false,
        });
    };
    if audit.tombstones_applied {
        return Ok(audit);
    }

    let conn = open_db(db).map_err(|e| e.to_string())?;
    let _pending_removed = purge_pending_matching(&conn, &audit.query)?;
    let matching = docs_with_token_in_body(&conn, &audit.query).map_err(|e| e.to_string())?;

    audit.delete_gate_open = true;
    tombstone_docs(&conn, &matching).map_err(|e| e.to_string())?;
    clear_postings_for_docs(&conn, &matching).map_err(|e| e.to_string())?;
    audit.tombstones_applied = true;

    run_docstore_gc(&conn, &matching).map_err(|e| e.to_string())?;
    audit.docstore_gc_ran = true;

    save_delete_audit(state, &audit)?;
    Ok(audit)
}

pub fn pending_delete_applied(state: &Path) -> Result<bool, String> {
    match load_delete_audit(state)? {
        None => Ok(true),
        Some(audit) => Ok(audit.tombstones_applied),
    }
}
