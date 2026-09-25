use crate::model::Document;
use rusqlite::{params, Connection};
use std::path::Path;

pub fn open_db(path: &Path) -> rusqlite::Result<Connection> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).ok();
    }
    let conn = Connection::open(path)?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY,
            body TEXT NOT NULL,
            split_id TEXT
        );
        CREATE TABLE IF NOT EXISTS postings (
            token TEXT NOT NULL,
            doc_id INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tombstones (
            doc_id INTEGER PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS pending_docs (
            doc_id INTEGER PRIMARY KEY,
            body TEXT NOT NULL
        );",
    )?;
    Ok(conn)
}

pub fn insert_pending(conn: &Connection, doc: &Document) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT OR REPLACE INTO pending_docs (doc_id, body) VALUES (?1, ?2)",
        params![doc.doc_id, doc.body],
    )?;
    Ok(())
}

pub fn materialize_pending(conn: &Connection, split_id: &str) -> rusqlite::Result<i64> {
    let mut stmt = conn.prepare("SELECT doc_id, body FROM pending_docs ORDER BY doc_id")?;
    let rows: Vec<(i64, String)> = stmt
        .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))?
        .collect::<Result<_, _>>()?;
    for (doc_id, body) in &rows {
        conn.execute(
            "INSERT OR REPLACE INTO documents (doc_id, body, split_id) VALUES (?1, ?2, ?3)",
            params![doc_id, body, split_id],
        )?;
    }
    conn.execute("DELETE FROM pending_docs", [])?;
    Ok(rows.len() as i64)
}

pub fn docs_for_split(conn: &Connection, split_id: &str) -> rusqlite::Result<Vec<i64>> {
    let mut stmt =
        conn.prepare("SELECT doc_id FROM documents WHERE split_id = ?1 ORDER BY doc_id")?;
    let ids = stmt
        .query_map(params![split_id], |row| row.get(0))?
        .collect::<Result<Vec<i64>, _>>()?;
    Ok(ids)
}

pub fn reassign_split(conn: &Connection, from: &str, to: &str) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE documents SET split_id = ?1 WHERE split_id = ?2",
        params![to, from],
    )?;
    Ok(())
}

pub fn remove_split_docs(conn: &Connection, split_id: &str) -> rusqlite::Result<()> {
    conn.execute(
        "DELETE FROM documents WHERE split_id = ?1",
        params![split_id],
    )?;
    Ok(())
}

pub fn add_posting(conn: &Connection, token: &str, doc_id: i64) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT INTO postings (token, doc_id) VALUES (?1, ?2)",
        params![token, doc_id],
    )?;
    Ok(())
}

pub fn clear_postings_for_docs(conn: &Connection, doc_ids: &[i64]) -> rusqlite::Result<()> {
    for doc_id in doc_ids {
        conn.execute("DELETE FROM postings WHERE doc_id = ?1", params![doc_id])?;
    }
    Ok(())
}

pub fn tombstone_docs(conn: &Connection, doc_ids: &[i64]) -> rusqlite::Result<()> {
    for doc_id in doc_ids {
        conn.execute(
            "INSERT OR IGNORE INTO tombstones (doc_id) VALUES (?1)",
            params![doc_id],
        )?;
    }
    Ok(())
}

pub fn is_tombstoned(conn: &Connection, doc_id: i64) -> rusqlite::Result<bool> {
    let count: i64 = conn.query_row(
        "SELECT COUNT(*) FROM tombstones WHERE doc_id = ?1",
        params![doc_id],
        |row| row.get(0),
    )?;
    Ok(count > 0)
}

pub fn matching_docs(conn: &Connection, token: &str) -> rusqlite::Result<Vec<i64>> {
    let mut stmt = conn.prepare(
        "SELECT DISTINCT p.doc_id FROM postings p
         JOIN documents d ON d.doc_id = p.doc_id
         WHERE p.token = ?1 ORDER BY p.doc_id",
    )?;
    let ids = stmt
        .query_map(params![token], |row| row.get(0))?
        .collect::<Result<Vec<i64>, _>>()?;
    Ok(ids)
}

pub fn docs_with_token_in_body(conn: &Connection, token: &str) -> rusqlite::Result<Vec<i64>> {
    let mut stmt = conn.prepare("SELECT doc_id, body FROM documents ORDER BY doc_id")?;
    let rows = stmt.query_map([], |row| {
        Ok((row.get::<_, i64>(0)?, row.get::<_, String>(1)?))
    })?;
    let needle = token.to_lowercase();
    let mut out = Vec::new();
    for row in rows {
        let (doc_id, body) = row?;
        if body
            .split_whitespace()
            .any(|t| t.to_lowercase() == needle)
        {
            out.push(doc_id);
        }
    }
    Ok(out)
}
