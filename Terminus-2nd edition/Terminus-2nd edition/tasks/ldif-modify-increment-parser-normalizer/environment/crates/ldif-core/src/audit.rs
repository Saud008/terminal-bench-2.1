use std::path::Path;

use rusqlite::{params, Connection};

use crate::error::{LdifError, Result};
use crate::model::{AuditOperation, AuditQuery, AuditRow};

pub fn write_audit(path: &Path, seed: &str, rows: &[AuditRow]) -> Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|err| LdifError::Audit(err.to_string()))?;
    }
    let conn = Connection::open(path).map_err(|err| LdifError::Audit(err.to_string()))?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS audit_ops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed TEXT NOT NULL,
            seq INTEGER NOT NULL,
            dn TEXT NOT NULL,
            changetype TEXT NOT NULL,
            detail TEXT NOT NULL
        );",
    )
    .map_err(|err| LdifError::Audit(err.to_string()))?;
    conn.execute("DELETE FROM audit_ops WHERE seed = ?1", params![seed])
        .map_err(|err| LdifError::Audit(err.to_string()))?;
    for row in rows {
        conn.execute(
            "INSERT INTO audit_ops (seed, seq, dn, changetype, detail) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![seed, row.seq, row.dn, row.changetype, row.detail],
        )
        .map_err(|err| LdifError::Audit(err.to_string()))?;
    }
    Ok(())
}

pub fn query_audit(path: &Path, seed: &str) -> Result<AuditQuery> {
    let conn = Connection::open(path).map_err(|err| LdifError::Audit(err.to_string()))?;
    let mut stmt = conn
        .prepare(
            "SELECT seq, dn, changetype, detail FROM audit_ops WHERE seed = ?1 ORDER BY seq ASC",
        )
        .map_err(|err| LdifError::Audit(err.to_string()))?;
    let rows = stmt
        .query_map(params![seed], |row| {
            Ok(AuditOperation {
                seq: row.get::<_, i64>(0)? as u32,
                dn: row.get(1)?,
                changetype: row.get(2)?,
                detail: row.get(3)?,
            })
        })
        .map_err(|err| LdifError::Audit(err.to_string()))?;
    let mut operations = Vec::new();
    for row in rows {
        operations.push(row.map_err(|err| LdifError::Audit(err.to_string()))?);
    }
    Ok(AuditQuery {
        seed: seed.to_string(),
        operations,
    })
}
