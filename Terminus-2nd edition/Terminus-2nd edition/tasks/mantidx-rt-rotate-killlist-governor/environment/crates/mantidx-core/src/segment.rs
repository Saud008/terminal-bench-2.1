use crate::model::{RamSegmentMeta, RamSegmentsFile, RotateMeta};
use std::fs;
use std::path::{Path, PathBuf};

pub fn rotate_meta_path(state: &Path) -> PathBuf {
    state.join("rotate-meta.json")
}

pub fn ram_segments_path(state: &Path) -> PathBuf {
    state.join("ram-segments.json")
}

pub fn load_rotate_meta(state: &Path) -> Result<RotateMeta, String> {
    let path = rotate_meta_path(state);
    if !path.exists() {
        return Ok(RotateMeta {
            active_ram: vec!["ram-1".into()],
            disk_chunks: Vec::new(),
            rotate_seq: 0,
        });
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_rotate_meta(state: &Path, meta: &RotateMeta) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(meta).map_err(|e| e.to_string())?;
    fs::write(rotate_meta_path(state), raw).map_err(|e| e.to_string())
}

pub fn load_ram_segments(state: &Path) -> Result<RamSegmentsFile, String> {
    let path = ram_segments_path(state);
    if !path.exists() {
        return Ok(RamSegmentsFile {
            segments: vec![RamSegmentMeta {
                segment_id: "ram-1".into(),
                deleted_bitmap: Vec::new(),
                segment_order: 1,
            }],
        });
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_ram_segments(state: &Path, file: &RamSegmentsFile) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(file).map_err(|e| e.to_string())?;
    fs::write(ram_segments_path(state), raw).map_err(|e| e.to_string())
}

pub fn current_ram_segment(state: &Path) -> Result<String, String> {
    let meta = load_rotate_meta(state)?;
    meta.active_ram
        .last()
        .cloned()
        .ok_or_else(|| "no active ram segment".into())
}

pub fn next_ram_segment_id(state: &Path) -> Result<String, String> {
    let file = load_ram_segments(state)?;
    let n = file.segments.len() as i64 + 1;
    Ok(format!("ram-{n}"))
}

pub fn next_disk_chunk_id(state: &Path) -> Result<String, String> {
    let meta = load_rotate_meta(state)?;
    let n = meta.disk_chunks.len() as i64 + 1;
    Ok(format!("disk-{n}"))
}
