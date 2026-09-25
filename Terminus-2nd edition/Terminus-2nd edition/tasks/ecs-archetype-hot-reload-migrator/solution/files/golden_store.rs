use crate::model::{EntityRow, MigrationReport, ReportArchetype, ReportChunk, ReportStep};
use crate::{archetype, checksum, chunk_store, entity_id, journal, layout, migrator};
use anyhow::{Context, Result};
use rusqlite::{Connection, params};
use std::fs;
use std::path::Path;

pub fn open_db(path: &Path) -> Result<Connection> {
    let conn = Connection::open(path).with_context(|| format!("open db {}", path.display()))?;
    conn.execute_batch(
        "PRAGMA foreign_keys = ON;
         CREATE TABLE IF NOT EXISTS entities (
           stable_id INTEGER PRIMARY KEY,
           archetype_id INTEGER NOT NULL,
           chunk_id INTEGER NOT NULL,
           slot INTEGER NOT NULL,
           alive INTEGER NOT NULL
         );
         CREATE TABLE IF NOT EXISTS archetypes (
           archetype_id INTEGER PRIMARY KEY,
           signature TEXT NOT NULL,
           entity_count INTEGER NOT NULL
         );
         CREATE TABLE IF NOT EXISTS tombstones (
           stable_id INTEGER PRIMARY KEY,
           tombstoned_at TEXT NOT NULL
         );
         CREATE TABLE IF NOT EXISTS migration_state (
           id INTEGER PRIMARY KEY CHECK (id = 1),
           layout_version INTEGER NOT NULL,
           journal_status TEXT NOT NULL,
           commit_cursor INTEGER NOT NULL
         );",
    )?;
    Ok(conn)
}

pub fn apply_migration(
    db_path: &Path,
    chunks_dir: &Path,
    layout_path: &Path,
    journal_path: &Path,
    report_path: &Path,
) -> Result<()> {
    let manifest = layout::load_layout(layout_path)?;
    crate::validate::validate_manifest(&manifest)?;
    let journal = journal::load_journal(journal_path)?;
    let replay_from = journal::replay_start_cursor(&journal);
    let conn = open_db(db_path)?;

    let (applied_raw, entities_moved) =
        migrator::apply_steps(&conn, chunks_dir, &manifest, replay_from)?;
    let ids_remapped = if applied_raw.is_empty() {
        0
    } else {
        archetype::rebuild_archetype_table(&conn, &manifest, chunks_dir)?;
        entity_id::remap_new_entity_ids(&conn)?
    };

    let mut steps_applied = Vec::new();
    for (order, op, component, chunks_touched) in applied_raw {
        steps_applied.push(ReportStep {
            order,
            op,
            component,
            chunks_touched,
        });
    }

    let mut archetypes = Vec::new();
    let mut stmt = conn.prepare("SELECT archetype_id, signature, entity_count FROM archetypes ORDER BY archetype_id")?;
    let rows = stmt.query_map([], |row| {
        Ok(ReportArchetype {
            archetype_id: row.get::<_, i64>(0)? as u32,
            signature: row.get(1)?,
            entity_count: row.get::<_, i64>(2)? as u32,
        })
    })?;
    for row in rows {
        archetypes.push(row?);
    }

    let mut chunks = Vec::new();
    for chunk_id in chunk_store::list_chunk_ids(chunks_dir)? {
        let (_, entities) = chunk_store::read_chunk(chunks_dir, chunk_id)?;
        let mut payload = Vec::new();
        let stride = layout::component_stride(&manifest) as usize;
        for ent in &entities {
            payload.extend_from_slice(&ent.stable_id.to_be_bytes());
            let mut body = ent.payload.clone();
            body.resize(stride, 0);
            payload.extend_from_slice(&body);
        }
        let checksum = checksum::chunk_checksum(chunk_id, manifest.to_version, &payload);
        chunks.push(ReportChunk {
            chunk_id,
            checksum,
            entity_count: entities.len() as u32,
        });
    }

    let report = MigrationReport {
        layout_id: manifest.layout_id.clone(),
        layout_version: manifest.to_version,
        steps_applied,
        archetypes,
        chunks,
        entities_moved,
        ids_remapped,
        journal_replayed_from: replay_from,
    };

    if let Some(parent) = report_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(report_path, serde_json::to_string_pretty(&report)?)?;

    conn.execute(
        "INSERT INTO migration_state (id, layout_version, journal_status, commit_cursor)
         VALUES (1, ?1, 'committed', ?2)
         ON CONFLICT(id) DO UPDATE SET
           layout_version = excluded.layout_version,
           journal_status = excluded.journal_status,
           commit_cursor = excluded.commit_cursor",
        params![
            manifest.to_version as i64,
            journal.entries.iter().map(|e| e.step_order).max().unwrap_or(0) as i64
        ],
    )?;
    journal::mark_committed(journal_path, &journal)?;
    Ok(())
}

pub fn snapshot_entities(conn: &Connection) -> Result<Vec<EntityRow>> {
    let mut stmt = conn.prepare(
        "SELECT stable_id, archetype_id, chunk_id, slot, alive FROM entities ORDER BY stable_id",
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
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
    }
    Ok(out)
}
