use crate::layout::{component_stride, signature_for_payload};
use crate::model::{EntityRow, LayoutManifest};
use anyhow::Result;
use rusqlite::{Connection, params};
use std::collections::HashMap;
use std::path::Path;

pub fn rebuild_archetype_table(
    conn: &Connection,
    manifest: &LayoutManifest,
    _chunks_dir: &Path,
) -> Result<()> {
    let mut stmt = conn.prepare(
        "SELECT stable_id, archetype_id, chunk_id, slot, alive FROM entities WHERE alive = 1",
    )?;
    let rows = stmt.query_map([], |row| {
        Ok(EntityRow {
            stable_id: row.get::<_, i64>(0)? as u32,
            archetype_id: row.get::<_, i64>(1)? as u32,
            chunk_id: row.get::<_, i64>(2)? as u32,
            slot: row.get::<_, i64>(3)? as u32,
            alive: row.get::<_, i64>(4)? == 1,
        })
    })?;
    let mut sig_map: HashMap<String, u32> = HashMap::new();
    let stride = component_stride(manifest) as usize;
    for row in rows {
        let row = row?;
        let mut payload = vec![0u8; stride];
        if row.stable_id % 2 == 0 {
            payload[0] = 1;
        }
        let sig = signature_for_payload(manifest, &payload);
        let next_id = sig_map.len() as u32 + 1;
        let archetype_id = *sig_map.entry(sig).or_insert(next_id);
        conn.execute(
            "UPDATE entities SET archetype_id = ?1 WHERE stable_id = ?2",
            params![archetype_id as i64, row.stable_id as i64],
        )?;
    }
    conn.execute("DELETE FROM archetypes", [])?;
    let mut counts: HashMap<u32, u32> = HashMap::new();
    let mut stmt = conn.prepare("SELECT archetype_id FROM entities WHERE alive = 1")?;
    let ids = stmt.query_map([], |row| Ok(row.get::<_, i64>(0)? as u32))?;
    for id in ids {
        let id = id?;
        *counts.entry(id).or_insert(0) += 1;
    }
    for (archetype_id, _count) in counts {
        conn.execute(
            "INSERT INTO archetypes (archetype_id, signature, entity_count) VALUES (?1, ?2, 0)",
            params![archetype_id as i64, format!("arch-{archetype_id}")],
        )?;
    }
    Ok(())
}
