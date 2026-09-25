use crate::chunk_store::{list_chunk_ids, read_chunk};
use crate::layout::{component_stride, signature_for_payload};
use crate::model::{EntityRow, LayoutManifest};
use anyhow::Result;
use rusqlite::{Connection, params};
use std::collections::HashMap;
use std::path::Path;

pub fn rebuild_archetype_table(
    conn: &Connection,
    manifest: &LayoutManifest,
    chunks_dir: &Path,
) -> Result<()> {
    let stride = component_stride(manifest) as usize;
    let mut payload_by_slot: HashMap<(u32, u32), Vec<u8>> = HashMap::new();
    for chunk_id in list_chunk_ids(chunks_dir)? {
        let (_, entities) = read_chunk(chunks_dir, chunk_id)?;
        for (slot, ent) in entities.iter().enumerate() {
            let mut body = ent.payload.clone();
            body.resize(stride, 0);
            payload_by_slot.insert((chunk_id, slot as u32), body);
        }
    }

    let mut stmt = conn.prepare(
        "SELECT stable_id, archetype_id, chunk_id, slot, alive FROM entities WHERE alive = 1 ORDER BY stable_id ASC",
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

    let mut sig_to_id: HashMap<String, u32> = HashMap::new();
    let mut next_id = 1u32;
    let mut counts: HashMap<u32, u32> = HashMap::new();
    let mut sig_by_id: HashMap<u32, String> = HashMap::new();

    for row in rows {
        let row = row?;
        let payload = payload_by_slot
            .get(&(row.chunk_id, row.slot))
            .cloned()
            .unwrap_or_else(|| vec![0u8; stride]);
        let sig = signature_for_payload(manifest, &payload);
        let archetype_id = if let Some(id) = sig_to_id.get(&sig) {
            *id
        } else {
            let id = next_id;
            sig_to_id.insert(sig.clone(), id);
            sig_by_id.insert(id, sig);
            next_id += 1;
            id
        };
        conn.execute(
            "UPDATE entities SET archetype_id = ?1 WHERE stable_id = ?2",
            params![archetype_id as i64, row.stable_id as i64],
        )?;
        *counts.entry(archetype_id).or_insert(0) += 1;
    }

    conn.execute("DELETE FROM archetypes", [])?;
    let mut ids: Vec<u32> = counts.keys().copied().collect();
    ids.sort_unstable();
    for archetype_id in ids {
        let count = counts.get(&archetype_id).copied().unwrap_or(0);
        let signature = sig_by_id
            .get(&archetype_id)
            .cloned()
            .unwrap_or_else(|| format!("arch-{archetype_id}"));
        conn.execute(
            "INSERT INTO archetypes (archetype_id, signature, entity_count) VALUES (?1, ?2, ?3)",
            params![archetype_id as i64, signature, count as i64],
        )?;
    }
    Ok(())
}
