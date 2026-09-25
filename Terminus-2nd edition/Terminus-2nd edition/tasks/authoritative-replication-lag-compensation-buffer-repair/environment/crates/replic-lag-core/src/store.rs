//! SQLite persistence for replication lag simulation state.

use rusqlite::{params, Connection};
use std::path::Path;

pub struct LagStore {
    conn: Connection,
}

impl LagStore {
    pub fn open(path: &Path) -> Result<Self, rusqlite::Error> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).ok();
        }
        let conn = Connection::open(path)?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS snapshot_deltas (
                snapshot_seq INTEGER PRIMARY KEY,
                base_seq INTEGER NOT NULL,
                state_xor INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merged_hash INTEGER NOT NULL,
                integrity_chain INTEGER NOT NULL
            );",
        )?;
        Ok(Self { conn })
    }

    pub fn get_meta(&self, key: &str) -> Result<u64, rusqlite::Error> {
        let val: Option<i64> = self
            .conn
            .query_row(
                "SELECT value FROM meta WHERE key = ?1",
                params![key],
                |row| row.get(0),
            )
            .optional()?;
        Ok(val.unwrap_or(0) as u64)
    }

    pub fn set_meta(&self, key: &str, value: u64) -> Result<(), rusqlite::Error> {
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES(?1, ?2)
             ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            params![key, value as i64],
        )?;
        Ok(())
    }

    pub fn insert_snapshot_delta(
        &self,
        snapshot_seq: u64,
        base_seq: u64,
        state_xor: u64,
    ) -> Result<(), rusqlite::Error> {
        self.conn.execute(
            "INSERT OR REPLACE INTO snapshot_deltas(snapshot_seq, base_seq, state_xor)
             VALUES(?1, ?2, ?3)",
            params![snapshot_seq as i64, base_seq as i64, state_xor as i64],
        )?;
        Ok(())
    }

    pub fn load_snapshot_deltas(&self) -> Result<Vec<(u64, u64, u64)>, rusqlite::Error> {
        let mut stmt = self
            .conn
            .prepare("SELECT snapshot_seq, base_seq, state_xor FROM snapshot_deltas ORDER BY snapshot_seq")?;
        let rows = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, i64>(0)? as u64,
                    row.get::<_, i64>(1)? as u64,
                    row.get::<_, i64>(2)? as u64,
                ))
            })?
            .collect::<Result<Vec<_>, _>>()?;
        Ok(rows)
    }

    pub fn gap_event_count(&self) -> Result<u64, rusqlite::Error> {
        Ok(self.get_meta("gap_events")?)
    }

    pub fn bump_gap_events(&self) -> Result<(), rusqlite::Error> {
        let cur = self.get_meta("gap_events")?;
        self.set_meta("gap_events", cur + 1)
    }

    pub fn integrity_seed(&self) -> Result<u64, rusqlite::Error> {
        Ok(self.get_meta("integrity_seed")?)
    }

    pub fn record_export(
        &self,
        merged_hash: u64,
        integrity_chain: u64,
    ) -> Result<i64, rusqlite::Error> {
        self.conn.execute(
            "INSERT INTO exports(merged_hash, integrity_chain) VALUES(?1, ?2)",
            params![merged_hash as i64, integrity_chain as i64],
        )?;
        Ok(self.conn.last_insert_rowid())
    }
}

use rusqlite::OptionalExtension;
