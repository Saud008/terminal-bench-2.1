use rusqlite::{Connection, Result};

pub fn open_db(path: &str) -> Result<Connection> {
    let conn = Connection::open(path)?;
    conn.execute_batch(
        "PRAGMA foreign_keys = ON;
         CREATE TABLE IF NOT EXISTS meta (
           key TEXT PRIMARY KEY,
           value TEXT NOT NULL
         );
         CREATE TABLE IF NOT EXISTS slots (
           slot INTEGER PRIMARY KEY,
           item TEXT NOT NULL,
           qty INTEGER NOT NULL CHECK(qty > 0)
         );
         CREATE TABLE IF NOT EXISTS craft_log (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           recipe_id TEXT NOT NULL,
           batch_qty INTEGER NOT NULL,
           committed INTEGER NOT NULL
         );",
    )?;
    Ok(conn)
}
