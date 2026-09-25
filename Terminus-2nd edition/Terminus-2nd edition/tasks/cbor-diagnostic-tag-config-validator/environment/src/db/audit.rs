use rusqlite::{params, Connection};

use crate::model::types::StagingSnapshot;

const DB_PATH: &str = "/app/state/audit.db";

pub struct AuditStore {
    conn: Connection,
}

impl AuditStore {
    pub fn open() -> Result<Self, String> {
        if let Some(parent) = std::path::Path::new(DB_PATH).parent() {
            std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        let conn = Connection::open(DB_PATH).map_err(|e| e.to_string())?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bundle_id TEXT NOT NULL,
                action TEXT NOT NULL,
                policy TEXT NOT NULL,
                nonce BLOB NOT NULL,
                tags_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );",
        )
        .map_err(|e| e.to_string())?;
        Ok(Self { conn })
    }

    pub fn record_ingest(&self, snapshot: &StagingSnapshot) -> Result<(), String> {
        let tags_json =
            serde_json::to_string(&snapshot.diagnostic_tags).map_err(|e| e.to_string())?;
        self.conn
            .execute(
                "INSERT INTO audit (bundle_id, action, policy, nonce, tags_json) VALUES (?1, 'ingest', ?2, ?3, ?4)",
                params![
                    snapshot.bundle_id,
                    snapshot.envelope.policy,
                    snapshot.envelope.nonce,
                    tags_json,
                ],
            )
            .map_err(|e| e.to_string())?;
        Ok(())
    }

    pub fn record_revalidate(&self, snapshot: &StagingSnapshot) -> Result<(), String> {
        self.record_ingest(snapshot)
    }

    pub fn count_for_bundle(&self, bundle_id: &str) -> Result<u64, String> {
        let count: i64 = self
            .conn
            .query_row(
                "SELECT COUNT(*) FROM audit WHERE bundle_id = ?1 AND action = 'ingest'",
                params![bundle_id],
                |row| row.get(0),
            )
            .map_err(|e| e.to_string())?;
        Ok(count as u64)
    }

    pub fn latest_snapshot(&self) -> Result<StagingSnapshot, String> {
        self.conn
            .query_row(
                "SELECT bundle_id, policy, nonce, tags_json FROM audit ORDER BY id DESC LIMIT 1",
                [],
                |row| {
                    let bundle_id: String = row.get(0)?;
                    let policy: String = row.get(1)?;
                    let nonce: Vec<u8> = row.get(2)?;
                    let tags_json: String = row.get(3)?;
                    let diagnostic_tags: Vec<crate::model::types::DiagnosticTag> =
                        serde_json::from_str(&tags_json).map_err(|e| {
                            rusqlite::Error::ToSqlConversionFailure(Box::new(std::io::Error::new(
                                std::io::ErrorKind::InvalidData,
                                e.to_string(),
                            )))
                        })?;
                    Ok(StagingSnapshot {
                        bundle_id,
                        diagnostic_tags,
                        envelope: crate::model::types::PolicyEnvelope { policy, nonce },
                        version: 1,
                    })
                },
            )
            .map_err(|e| e.to_string())
    }
}
