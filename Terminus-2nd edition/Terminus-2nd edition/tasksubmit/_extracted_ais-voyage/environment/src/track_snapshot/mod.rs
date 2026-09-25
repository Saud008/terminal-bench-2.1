use std::fs;

use crate::voyage_err::SegmentError;
use crate::maritime_types::SnapshotFile;

pub fn write_snapshot(path: &str, snap: &SnapshotFile) -> Result<(), SegmentError> {
    if let Some(parent) = std::path::Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| SegmentError::Io(e.to_string()))?;
    }
    let json = serde_json::to_string_pretty(snap).map_err(|e| SegmentError::Parse(e.to_string()))?;
    fs::write(path, json).map_err(|e| SegmentError::Io(e.to_string()))
}

pub fn read_snapshot(path: &str) -> Result<SnapshotFile, SegmentError> {
    let raw = fs::read_to_string(path).map_err(|e| SegmentError::Io(e.to_string()))?;
    serde_json::from_str(&raw).map_err(|_| SegmentError::InvalidSnapshot)
}
