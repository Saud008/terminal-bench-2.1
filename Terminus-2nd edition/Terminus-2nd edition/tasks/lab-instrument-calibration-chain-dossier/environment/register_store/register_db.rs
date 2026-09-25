use crate::chain_schema::StagedInstrument;
use rusqlite::{params, Connection};
use std::path::Path;

pub fn ensure_register(path: &str) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let conn = Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS calibration_register (
            batch_id TEXT PRIMARY KEY,
            pack TEXT NOT NULL,
            fuse_generation INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );",
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn read_generation(path: &str, batch_id: &str) -> i32 {
    let Ok(conn) = Connection::open(path) else {
        return 0;
    };
    let Ok(mut stmt) = conn.prepare(
        "SELECT fuse_generation FROM calibration_register WHERE batch_id = ?1",
    ) else {
        return 0;
    };
    let Ok(gen) = stmt.query_row(params![batch_id], |row| row.get::<_, i32>(0)) else {
        return 0;
    };
    gen
}

pub fn upsert_row(
    path: &str,
    batch_id: &str,
    pack: &str,
    generation: i32,
    instrument: &StagedInstrument,
) -> Result<(), String> {
    ensure_register(path)?;
    let payload = serde_json::to_string(instrument).map_err(|e| e.to_string())?;
    let conn = Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO calibration_register (batch_id, pack, fuse_generation, payload_json)
         VALUES (?1, ?2, ?3, ?4)
         ON CONFLICT(batch_id) DO UPDATE SET
           pack = excluded.pack,
           fuse_generation = excluded.fuse_generation,
           payload_json = excluded.payload_json",
        params![batch_id, pack, generation, payload],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn load_active(path: &str, batch_id: &str) -> Result<StagedInstrument, String> {
    let conn = Connection::open(path).map_err(|e| e.to_string())?;
    let payload: String = conn
        .query_row(
            "SELECT payload_json FROM calibration_register WHERE batch_id = ?1",
            params![batch_id],
            |row| row.get(0),
        )
        .map_err(|e| e.to_string())?;
    serde_json::from_str(&payload).map_err(|e| e.to_string())
}
