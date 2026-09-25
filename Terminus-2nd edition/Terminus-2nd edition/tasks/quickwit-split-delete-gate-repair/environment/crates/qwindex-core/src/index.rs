//! Token indexing helpers.

use crate::store::{add_posting, open_db};
use std::path::Path;

pub fn tokenize(body: &str) -> Vec<String> {
    body.split_whitespace()
        .map(|t| t.to_lowercase())
        .collect()
}

pub fn index_document(db: &Path, doc_id: i64, body: &str) -> Result<(), String> {
    let conn = open_db(db).map_err(|e| e.to_string())?;
    for token in tokenize(body) {
        add_posting(&conn, &token, doc_id).map_err(|e| e.to_string())?;
    }
    Ok(())
}

pub fn index_pending_batch(db: &Path, split_id: &str) -> Result<(), String> {
    let conn = open_db(db).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT doc_id, body FROM documents WHERE split_id = ?1")
        .map_err(|e| e.to_string())?;
    let rows: Vec<(i64, String)> = stmt
        .query_map(rusqlite::params![split_id], |row| {
            Ok((row.get(0)?, row.get(1)?))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<_, _>>()
        .map_err(|e| e.to_string())?;
    for (doc_id, body) in rows {
        for token in tokenize(&body) {
            add_posting(&conn, &token, doc_id).map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}
