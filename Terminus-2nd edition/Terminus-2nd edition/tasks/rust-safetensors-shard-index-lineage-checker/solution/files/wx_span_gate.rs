use crate::wx_frame_parse::{data_section_len, ParsedShard, TensorHeader};
use std::path::Path;

pub fn wx_guard_window(_shard_path: &Path, header: &TensorHeader, shard: &ParsedShard) -> Result<(), String> {
    let data_len = data_section_len(shard);
    let (start, end) = (header.data_offsets[0], header.data_offsets[1]);
    if end > data_len {
        return Err(format!("offset end {end} exceeds data section {data_len}"));
    }
    if start > end {
        return Err("offset start after end".into());
    }
    Ok(())
}
