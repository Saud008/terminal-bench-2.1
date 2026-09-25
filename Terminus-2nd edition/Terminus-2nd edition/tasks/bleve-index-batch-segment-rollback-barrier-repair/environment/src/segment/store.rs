use crate::errors::BleveError;
use crate::model::SegmentData;
use crate::state::fs::{load_root_map, save_root_map};
use std::fs;
use std::path::{Path, PathBuf};

pub fn segment_path(root: &Path, segment_id: u64) -> PathBuf {
    root.join("segments").join(format!("seg-{segment_id}.json"))
}

pub fn write_segment(root: &Path, segment: &SegmentData) -> Result<PathBuf, BleveError> {
    let path = segment_path(root, segment.segment_id);
    fs::write(&path, format!("{}\n", serde_json::to_string_pretty(segment)?))?;

    let mut map = load_root_map(root)?;
    map.segments.push(path.file_name().unwrap().to_string_lossy().to_string());
    save_root_map(root, &map)?;
    Ok(path)
}

pub fn rollback_segment(root: &Path, segment_id: u64) -> Result<(), BleveError> {
    let path = segment_path(root, segment_id);
    if path.exists() {
        fs::remove_file(path)?;
    }
    Ok(())
}

pub fn read_segment(root: &Path, segment_file: &str) -> Result<SegmentData, BleveError> {
    let path = root.join("segments").join(segment_file);
    Ok(serde_json::from_str(&fs::read_to_string(path)?)?)
}
