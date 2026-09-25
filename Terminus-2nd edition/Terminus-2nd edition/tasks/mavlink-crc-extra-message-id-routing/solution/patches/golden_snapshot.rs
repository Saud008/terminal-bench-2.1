use std::path::PathBuf;

use crate::error::{MavError, Result};
use crate::model::{DecodeSnapshot, DiffRow, ValidatedFrame};

pub fn decode_snapshot_path() -> PathBuf {
    PathBuf::from("/app/state/decode.snapshot.json")
}

pub fn write_decode_snapshot(
    frames: &[ValidatedFrame],
    seed: &str,
    checkpoint_frame_count: u32,
    deduped_count: u32,
    stale_seq_dropped: u32,
    diff_rows: &[DiffRow],
) -> Result<()> {
    let path = decode_snapshot_path();
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| MavError::Publish(e.to_string()))?;
    }
    let snap = DecodeSnapshot {
        version: 1,
        seed: seed.to_string(),
        checkpoint_frame_count,
        deduped_count,
        stale_seq_dropped,
        changed_fact_count: diff_rows.len() as u32,
        diff_rows: diff_rows.to_vec(),
        frames: frames.to_vec(),
    };
    let json = serde_json::to_string_pretty(&snap).map_err(|e| MavError::Publish(e.to_string()))?;
    std::fs::write(path, format!("{json}\n")).map_err(|e| MavError::Publish(e.to_string()))?;
    Ok(())
}

pub fn read_decode_snapshot() -> Result<DecodeSnapshot> {
    let path = decode_snapshot_path();
    if !path.is_file() {
        return Err(MavError::Publish("decode snapshot missing".into()));
    }
    let text = std::fs::read_to_string(&path).map_err(|e| MavError::Publish(e.to_string()))?;
    serde_json::from_str(&text).map_err(|e| MavError::Publish(e.to_string()))
}
