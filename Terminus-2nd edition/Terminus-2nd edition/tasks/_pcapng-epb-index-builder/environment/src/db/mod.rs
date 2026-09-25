use rusqlite::{params, Connection};

#[derive(Debug, Clone)]
pub struct PacketRow {
    pub interface_id: u32,
    pub ts_ns: u64,
    pub file_offset: u64,
    pub cap_len: u32,
    pub packet_len: u32,
}

pub struct Store {
    conn: Connection,
}

impl Store {
    pub fn open(path: &str) -> rusqlite::Result<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch(include_str!("schema.sql"))?;
        Ok(Self { conn })
    }

    pub fn upsert_iface(&self, interface_id: u32, name: &str) -> rusqlite::Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO iface_meta (interface_id, if_name) VALUES (?1, ?2)",
            params![interface_id, name],
        )?;
        Ok(())
    }

    pub fn insert_packet(
        &mut self,
        interface_id: u32,
        ts_ns: u64,
        file_offset: u64,
        cap_len: u32,
        packet_len: u32,
        replay_key: &str,
    ) -> rusqlite::Result<bool> {
        let exists: i64 = self.conn.query_row(
            "SELECT COUNT(1) FROM replay_keys WHERE replay_key = ?1",
            params![replay_key],
            |row| row.get(0),
        )?;
        if exists > 0 {
            self.conn.execute(
                "UPDATE ingest_stats SET duplicate_rejected = duplicate_rejected + 1 WHERE id = 1",
                [],
            )?;
            return Ok(false);
        }
        self.conn.execute(
            "INSERT INTO packet (interface_id, ts_ns, file_offset, cap_len, packet_len)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![interface_id, ts_ns, file_offset, cap_len, packet_len],
        )?;
        self.conn.execute(
            "INSERT INTO replay_keys (replay_key) VALUES (?1)",
            params![replay_key],
        )?;
        self.conn.execute(
            "UPDATE ingest_stats SET accepted = accepted + 1 WHERE id = 1",
            [],
        )?;
        Ok(true)
    }

    pub fn record_crc_reject(&mut self) -> rusqlite::Result<()> {
        self.conn.execute(
            "UPDATE ingest_stats SET crc_rejected = crc_rejected + 1 WHERE id = 1",
            [],
        )?;
        Ok(())
    }

    pub fn all_packets(&self) -> rusqlite::Result<Vec<PacketRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT interface_id, ts_ns, file_offset, cap_len, packet_len
             FROM packet ORDER BY file_offset, interface_id, ts_ns",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(PacketRow {
                interface_id: row.get(0)?,
                ts_ns: row.get(1)?,
                file_offset: row.get(2)?,
                cap_len: row.get(3)?,
                packet_len: row.get(4)?,
            })
        })?;
        rows.collect()
    }

    pub fn iface_meta(&self) -> rusqlite::Result<Vec<(u32, String)>> {
        let mut stmt = self
            .conn
            .prepare("SELECT interface_id, if_name FROM iface_meta ORDER BY interface_id")?;
        let rows = stmt.query_map([], |row| Ok((row.get(0)?, row.get(1)?)))?;
        rows.collect()
    }

    pub fn ingest_stats(&self) -> rusqlite::Result<(i64, i64, i64)> {
        self.conn.query_row(
            "SELECT crc_rejected, duplicate_rejected, accepted FROM ingest_stats WHERE id = 1",
            [],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )
    }
}
