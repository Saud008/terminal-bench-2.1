use rusqlite::{params, Connection};
use std::path::Path;

pub fn open_db(db: &Path) -> rusqlite::Result<Connection> {
    if let Some(parent) = db.parent() {
        std::fs::create_dir_all(parent).ok();
    }
    let conn = Connection::open(db)?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS docs (
            doc_id INTEGER PRIMARY KEY,
            body TEXT NOT NULL,
            segment_id TEXT NOT NULL,
            tier TEXT NOT NULL,
            killed INTEGER NOT NULL DEFAULT 0,
            price INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS binlog_pending (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            committed INTEGER NOT NULL DEFAULT 0
        );",
    )?;
    Ok(conn)
}

pub fn insert_doc(
    conn: &Connection,
    doc_id: i64,
    body: &str,
    segment_id: &str,
    tier: &str,
) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT OR REPLACE INTO docs (doc_id, body, segment_id, tier, killed, price)
         VALUES (?1, ?2, ?3, ?4, 0, 0)",
        params![doc_id, body, segment_id, tier],
    )?;
    Ok(())
}

pub fn enqueue_binlog(conn: &Connection, doc_id: i64, body: &str) -> rusqlite::Result<i64> {
    conn.execute(
        "INSERT INTO binlog_pending (doc_id, body, committed) VALUES (?1, ?2, 0)",
        params![doc_id, body],
    )?;
    Ok(conn.last_insert_rowid())
}

pub fn mark_killed(conn: &Connection, doc_id: i64) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE docs SET killed = 1 WHERE doc_id = ?1",
        params![doc_id],
    )?;
    Ok(())
}

pub fn docs_matching(conn: &Connection, token: &str) -> rusqlite::Result<Vec<(i64, String, String, i64)>> {
    let mut stmt = conn.prepare(
        "SELECT doc_id, body, segment_id, killed FROM docs WHERE body LIKE '%' || ?1 || '%'",
    )?;
    let rows = stmt.query_map(params![token], |row| {
        Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?))
    })?;
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
    }
    Ok(out)
}

pub fn docs_for_segment(conn: &Connection, segment_id: &str) -> rusqlite::Result<Vec<(i64, String, i64)>> {
    let mut stmt = conn.prepare(
        "SELECT doc_id, body, killed FROM docs WHERE segment_id = ?1 ORDER BY doc_id",
    )?;
    let rows = stmt.query_map(params![segment_id], |row| {
        Ok((row.get(0)?, row.get(1)?, row.get(2)?))
    })?;
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
    }
    Ok(out)
}

pub fn reassign_segment(conn: &Connection, from: &str, to: &str, tier: &str) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE docs SET segment_id = ?1, tier = ?2 WHERE segment_id = ?3",
        params![to, tier, from],
    )?;
    Ok(())
}

pub fn update_price(conn: &Connection, doc_id: i64, price: i64) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE docs SET price = ?1 WHERE doc_id = ?2",
        params![price, doc_id],
    )?;
    Ok(())
}

pub fn is_killed(conn: &Connection, doc_id: i64) -> rusqlite::Result<bool> {
    let killed: i64 = conn.query_row(
        "SELECT killed FROM docs WHERE doc_id = ?1",
        params![doc_id],
        |row| row.get(0),
    )?;
    Ok(killed != 0)
}

pub fn doc_tier(conn: &Connection, doc_id: i64) -> rusqlite::Result<String> {
    conn.query_row(
        "SELECT tier FROM docs WHERE doc_id = ?1",
        params![doc_id],
        |row| row.get(0),
    )
}

pub fn pending_binlog_count(conn: &Connection) -> rusqlite::Result<i64> {
    conn.query_row(
        "SELECT COUNT(*) FROM binlog_pending WHERE committed = 0",
        [],
        |row| row.get(0),
    )
}

pub fn commit_all_pending(conn: &Connection) -> rusqlite::Result<i64> {
    let updated = conn.execute(
        "UPDATE binlog_pending SET committed = 1 WHERE committed = 0",
        [],
    )?;
    Ok(updated as i64)
}

pub fn max_binlog_seq(conn: &Connection) -> rusqlite::Result<i64> {
    conn.query_row(
        "SELECT COALESCE(MAX(seq), 0) FROM binlog_pending",
        [],
        |row| row.get(0),
    )
}

pub fn discard_uncommitted_pending(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute("DELETE FROM binlog_pending WHERE committed = 0", [])?;
    Ok(())
}

pub fn searchable_hits(conn: &Connection, token: &str) -> rusqlite::Result<Vec<i64>> {
    let mut stmt = conn.prepare(
        "SELECT doc_id FROM docs
         WHERE body LIKE '%' || ?1 || '%' AND killed = 0
         ORDER BY doc_id",
    )?;
    let rows = stmt.query_map(params![token], |row| row.get(0))?;
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
       }
    Ok(out)
}
