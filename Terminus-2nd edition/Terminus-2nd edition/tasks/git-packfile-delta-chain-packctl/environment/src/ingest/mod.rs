use std::fs;
use std::path::Path;

use crate::staging;
use crate::types::{CatalogEntry, PackCatalog, PackStage, StageObject};

pub fn ingest_directory(pack_dir: &str, stage_path: &str) -> Result<(), String> {
    let dir = Path::new(pack_dir);
    let catalog_path = dir.join("catalog.json");
    let stream_path = dir.join("pack.stream");
    if !catalog_path.is_file() {
        return Err(format!("missing catalog.json in {pack_dir}"));
    }
    if !stream_path.is_file() {
        return Err(format!("missing pack.stream in {pack_dir}"));
    }

    let raw = fs::read_to_string(&catalog_path).map_err(|e| e.to_string())?;
    let catalog: PackCatalog = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let seq = staging::bump_ingest_seq(stage_path);

    let objects: Vec<StageObject> = catalog
        .entries
        .iter()
        .enumerate()
        .map(|(idx, e)| stage_row(e, idx as u32))
        .collect();

    let stage = PackStage {
        pack_id: catalog.pack_id.clone(),
        ingest_seq: seq,
        pack_stream_path: stream_path.to_string_lossy().into_owned(),
        objects,
    };
    staging::save_stage(stage_path, &stage)
}

fn stage_row(entry: &CatalogEntry, order: u32) -> StageObject {
    StageObject {
        id: entry.id.clone(),
        kind: entry.kind.clone(),
        pack_offset: entry.pack_offset,
        compressed_size: entry.compressed_size,
        base_id: entry.base_id.clone(),
        base_pack_offset: entry.base_pack_offset,
        catalog_order: order,
    }
}
