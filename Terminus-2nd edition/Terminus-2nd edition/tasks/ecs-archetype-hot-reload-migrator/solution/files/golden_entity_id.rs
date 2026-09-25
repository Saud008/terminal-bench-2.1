use anyhow::Result;
use rusqlite::{Connection, params};

pub fn remap_new_entity_ids(conn: &Connection) -> Result<u32> {
    let tombstones = tombstone_ids(conn)?;
    let tomb_set: std::collections::HashSet<u32> = tombstones.into_iter().collect();
    let max_id: i64 = conn.query_row(
        "SELECT COALESCE(MAX(stable_id), 0) FROM entities",
        [],
        |row| row.get(0),
    )?;
    let mut stmt = conn.prepare(
        "SELECT rowid FROM entities WHERE alive = 1 AND stable_id = 0 ORDER BY rowid ASC",
    )?;
    let rowids = stmt.query_map([], |row| Ok(row.get::<_, i64>(0)?))?;
    let mut remapped = 0u32;
    let mut next_id = max_id as u32 + 1;
    for rowid in rowids {
        let rowid = rowid?;
        while tomb_set.contains(&next_id) {
            next_id += 1;
        }
        conn.execute(
            "UPDATE entities SET stable_id = ?1 WHERE rowid = ?2",
            params![next_id as i64, rowid],
        )?;
        remapped += 1;
        next_id += 1;
    }
    Ok(remapped)
}

pub fn tombstone_ids(conn: &Connection) -> Result<Vec<u32>> {
    let mut stmt = conn.prepare("SELECT stable_id FROM tombstones ORDER BY stable_id")?;
    let rows = stmt.query_map([], |row| Ok(row.get::<_, i64>(0)? as u32))?;
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
    }
    Ok(out)
}
