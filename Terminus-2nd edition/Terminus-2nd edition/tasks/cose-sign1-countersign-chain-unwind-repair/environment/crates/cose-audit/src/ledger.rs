use crate::errors::AuditError;
use rusqlite::{params, Connection};
use std::path::Path;

pub struct Ledger {
    conn: Connection,
}

pub struct LedgerRow {
    pub sha256: String,
    pub cose_bytes: Vec<u8>,
    pub ingest_count: i64,
}

impl Ledger {
    pub fn open(path: &str) -> Result<Self, AuditError> {
        if let Some(parent) = Path::new(path).parent() {
            std::fs::create_dir_all(parent).map_err(|e| AuditError::Io(e.to_string()))?;
        }
        let conn = Connection::open(path).map_err(|e| AuditError::Ledger(e.to_string()))?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS ingested (
                sha256 TEXT PRIMARY KEY,
                cose BLOB NOT NULL,
                ingest_count INTEGER NOT NULL DEFAULT 1
            );",
        )
        .map_err(|e| AuditError::Ledger(e.to_string()))?;
        Ok(Self { conn })
    }

    pub fn upsert(&self, sha256: &str, cose: &[u8]) -> Result<i64, AuditError> {
        let existing: Option<i64> = self
            .conn
            .query_row(
                "SELECT ingest_count FROM ingested WHERE sha256 = ?1",
                params![sha256],
                |r| r.get(0),
            )
            .ok();
        if let Some(count) = existing {
            self.conn
                .execute(
                    "UPDATE ingested SET ingest_count = ?1 WHERE sha256 = ?2",
                    params![count, sha256],
                )
                .map_err(|e| AuditError::Ledger(e.to_string()))?;
            Ok(count)
        } else {
            self.conn
                .execute(
                    "INSERT INTO ingested (sha256, cose, ingest_count) VALUES (?1, ?2, 1)",
                    params![sha256, cose],
                )
                .map_err(|e| AuditError::Ledger(e.to_string()))?;
            Ok(1)
        }
    }

    pub fn all_rows(&self) -> Result<Vec<LedgerRow>, AuditError> {
        let mut stmt = self
            .conn
            .prepare("SELECT sha256, cose, ingest_count FROM ingested ORDER BY rowid ASC")
            .map_err(|e| AuditError::Ledger(e.to_string()))?;
        let rows = stmt
            .query_map([], |r| {
                Ok(LedgerRow {
                    sha256: r.get(0)?,
                    cose_bytes: r.get(1)?,
                    ingest_count: r.get(2)?,
                })
            })
            .map_err(|e| AuditError::Ledger(e.to_string()))?;
        let mut out = vec![];
        for row in rows {
            out.push(row.map_err(|e| AuditError::Ledger(e.to_string()))?);
        }
        Ok(out)
    }
}
