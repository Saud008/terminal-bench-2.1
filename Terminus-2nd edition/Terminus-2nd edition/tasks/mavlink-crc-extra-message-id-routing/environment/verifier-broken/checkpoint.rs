use std::path::Path;

use rusqlite::{params, Connection};

use crate::error::{MavError, Result};
use crate::model::ValidatedFrame;

const SCHEMA: &str = "
CREATE TABLE IF NOT EXISTS accepted_frames (
    seed TEXT NOT NULL,
    sysid INTEGER NOT NULL,
    compid INTEGER NOT NULL,
    msg_id INTEGER NOT NULL,
    seq INTEGER NOT NULL,
    name TEXT NOT NULL,
    payload BLOB NOT NULL,
    PRIMARY KEY (seed, sysid, compid, msg_id, seq)
);
";

pub fn load_checkpoint(path: &Path, seed: &str) -> Result<Vec<ValidatedFrame>> {
    if !path.exists() {
        return Ok(Vec::new());
    }
    let conn = Connection::open(path).map_err(|e| MavError::Checkpoint(e.to_string()))?;
    conn.execute_batch(SCHEMA)
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    // Broken: ignore seed filter — cross-seed resume contamination.
    let mut stmt = conn
        .prepare(
            "SELECT sysid, compid, msg_id, seq, name, payload FROM accepted_frames ORDER BY rowid",
        )
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    let rows = stmt
        .query_map([], |row| {
            Ok(ValidatedFrame {
                sysid: row.get::<_, i64>(0)? as u8,
                compid: row.get::<_, i64>(1)? as u8,
                msg_id: row.get::<_, i64>(2)? as u32,
                seq: row.get::<_, i64>(3)? as u8,
                name: row.get(4)?,
                payload: row.get(5)?,
            })
        })
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    let mut out = Vec::new();
    for row in rows {
        out.push(row.map_err(|e| MavError::Checkpoint(e.to_string()))?);
    }
    let _ = seed;
    Ok(out)
}

pub fn append_checkpoint(path: &Path, seed: &str, frames: &[ValidatedFrame]) -> Result<()> {
    if frames.is_empty() {
        return Ok(());
    }
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| MavError::Checkpoint(e.to_string()))?;
    }
    let conn = Connection::open(path).map_err(|e| MavError::Checkpoint(e.to_string()))?;
    conn.execute_batch(SCHEMA)
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    let tx = conn
        .unchecked_transaction()
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    for frame in frames {
        tx.execute(
            "INSERT OR IGNORE INTO accepted_frames (seed, sysid, compid, msg_id, seq, name, payload)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                seed,
                frame.sysid,
                frame.compid,
                frame.msg_id,
                frame.seq,
                frame.name,
                frame.payload,
            ],
        )
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    }
    tx.commit()
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    Ok(())
}

pub fn checkpoint_seen_keys(
    path: &Path,
    seed: &str,
) -> Result<std::collections::HashSet<(u8, u8, u32, u8)>> {
    let mut out = std::collections::HashSet::new();
    if !path.exists() {
        return Ok(out);
    }
    let conn = Connection::open(path).map_err(|e| MavError::Checkpoint(e.to_string()))?;
    conn.execute_batch(SCHEMA)
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    let mut stmt = conn
        .prepare("SELECT sysid, compid, msg_id, seq FROM accepted_frames WHERE seed = ?1")
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    let rows = stmt
        .query_map(params![seed], |row| {
            Ok((
                row.get::<_, i64>(0)? as u8,
                row.get::<_, i64>(1)? as u8,
                row.get::<_, i64>(2)? as u32,
                row.get::<_, i64>(3)? as u8,
            ))
        })
        .map_err(|e| MavError::Checkpoint(e.to_string()))?;
    for row in rows {
        out.insert(row.map_err(|e| MavError::Checkpoint(e.to_string()))?);
    }
    Ok(out)
}
