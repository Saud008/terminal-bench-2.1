use crate::delete::{apply_pending_deletes, pending_delete_applied};
use crate::index::index_pending_batch;
use crate::manifest::{append_split, load_manifest};
use crate::model::{SplitEntry, SplitMeta};
use crate::store::{materialize_pending, open_db, insert_pending, docs_for_split};
use crate::cache::HotCache;
use crate::model::Document;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;

pub fn resolve_batch(batch: &Path) -> Result<std::path::PathBuf, String> {
    if batch.exists() {
        return Ok(batch.to_path_buf());
    }
    if let Ok(dir) = std::env::var("TB3_DOCS_DIR") {
        let alt = Path::new(&dir).join(batch.file_name().unwrap_or_default());
        if alt.exists() {
            return Ok(alt);
        }
    }
    Err(format!("batch not found: {}", batch.display()))
}

pub fn index_batch(db: &Path, batch: &Path) -> Result<i64, String> {
    let path = resolve_batch(batch)?;
    let conn = open_db(db).map_err(|e| e.to_string())?;
    let file = fs::File::open(&path).map_err(|e| e.to_string())?;
    let reader = BufReader::new(file);
    let mut count = 0i64;
    for line in reader.lines() {
        let line = line.map_err(|e| e.to_string())?;
        if line.trim().is_empty() {
            continue;
        }
        let doc: Document = serde_json::from_str(&line).map_err(|e| e.to_string())?;
        insert_pending(&conn, &doc).map_err(|e| e.to_string())?;
        count += 1;
    }
    Ok(count)
}

pub fn publish_split(state: &Path, db: &Path) -> Result<String, String> {
    apply_pending_deletes(state, db)?;

    let split_id = uuid::Uuid::new_v4().to_string();
    let conn = open_db(db).map_err(|e| e.to_string())?;
    materialize_pending(&conn, &split_id).map_err(|e| e.to_string())?;
    index_pending_batch(db, &split_id)?;

    if !pending_delete_applied(state)? {
        return Err("pending delete not applied".into());
    }

    let live_count = docs_for_split(&conn, &split_id).map_err(|e| e.to_string())?.len() as i64;

    let manifest = load_manifest(state)?;
    let publish_seq = manifest.splits.len() as i64 + 1;
    append_split(
        state,
        SplitEntry {
            split_id: split_id.clone(),
            parent_split_id: None,
            doc_count: live_count,
            publish_seq,
        },
    )?;

    let doc_ids = docs_for_split(&conn, &split_id).map_err(|e| e.to_string())?;
    let mut cache = HotCache::new();
    cache.load_split(&split_id, doc_ids);

    let mut meta = if state.join("split-meta.json").exists() {
        let raw = fs::read_to_string(state.join("split-meta.json")).map_err(|e| e.to_string())?;
        serde_json::from_str(&raw).map_err(|e| e.to_string())?
    } else {
        SplitMeta {
            active_splits: Vec::new(),
            publish_seq: 0,
        }
    };
    meta.active_splits.push(split_id.clone());
    meta.publish_seq += 1;
    fs::write(
        state.join("split-meta.json"),
        serde_json::to_string_pretty(&meta).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    Ok(split_id)
}
