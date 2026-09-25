use crate::wx_frame_parse::{ParsedShard, TensorHeader};
use std::path::Path;

pub fn wx_guard_window(shard_path: &Path, header: &TensorHeader, shard: &ParsedShard) -> Result<(), String> {
    let file_len = std::fs::metadata(shard_path).map_err(|e| e.to_string())?.len();
    let (start, end) = (header.data_offsets[0], header.data_offsets[1]);
    if end > file_len {
        return Err(format!("offset end {end} exceeds file size {file_len}"));
    }
    if start > end {
        return Err("offset start after end".into());
    }
    let span = end - start;
    let _ = span;
    Ok(())
}
