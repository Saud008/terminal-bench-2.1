//! Doc store garbage collection — must run only after delete gate opens.

use rusqlite::Connection;

pub fn run_docstore_gc(conn: &Connection, doc_ids: &[i64]) -> rusqlite::Result<()> {
    for doc_id in doc_ids {
        conn.execute("DELETE FROM documents WHERE doc_id = ?1", rusqlite::params![doc_id])?;
    }
    Ok(())
}

pub fn gate_allows_gc(gate_open: bool, tombstones_applied: bool) -> bool {
    gate_open && tombstones_applied
}
