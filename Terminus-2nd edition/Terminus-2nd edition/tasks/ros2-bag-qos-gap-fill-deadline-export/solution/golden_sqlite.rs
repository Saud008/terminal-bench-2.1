use std::path::Path;

use anyhow::Result;
use rusqlite::{params, Connection};
use sha2::{Digest, Sha256};

use crate::model::Message;
use crate::qos::deadline::DeadlineMiss;

pub fn write_export(path: &Path, messages: &[Message], misses: &[DeadlineMiss]) -> Result<()> {
    if path.exists() {
        std::fs::remove_file(path)?;
    }
    let conn = Connection::open(path)?;
    conn.execute_batch(
        "CREATE TABLE messages (
            topic TEXT NOT NULL,
            seq INTEGER NOT NULL,
            publish_ns INTEGER NOT NULL,
            receive_ns INTEGER NOT NULL,
            payload_hash TEXT NOT NULL,
            synthetic INTEGER NOT NULL,
            PRIMARY KEY (topic, seq)
        );
        CREATE TABLE deadline_misses (
            topic TEXT NOT NULL,
            seq INTEGER NOT NULL,
            delta_ns INTEGER NOT NULL,
            deadline_ms INTEGER NOT NULL
        );",
    )?;
    for m in messages {
        let hash = payload_hash(&m.payload);
        conn.execute(
            "INSERT INTO messages (topic, seq, publish_ns, receive_ns, payload_hash, synthetic)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                m.topic,
                m.seq as i64,
                m.publish_ns as i64,
                m.receive_ns as i64,
                hash,
                if m.synthetic { 1 } else { 0 },
            ],
        )?;
    }
    for miss in misses {
        conn.execute(
            "INSERT INTO deadline_misses (topic, seq, delta_ns, deadline_ms)
             VALUES (?1, ?2, ?3, ?4)",
            params![
                miss.topic,
                miss.seq as i64,
                miss.delta_ns as i64,
                miss.deadline_ms as i64,
            ],
        )?;
    }
    Ok(())
}

fn payload_hash(data: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(data);
    hex::encode(h.finalize())
}
