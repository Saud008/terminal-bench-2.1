use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct BlockRecord {
    pub index: u32,
    pub block_type: String,
    #[serde(rename = "final")]
    pub final_block: bool,
    pub uncompressed_len: u16,
    pub block_checksum: u16,
}

#[derive(Debug, Clone, Serialize)]
pub struct StagingSnapshot {
    pub block_count: usize,
    pub blocks: Vec<BlockRecord>,
    pub window_size: u32,
    pub staging_adler: u32,
}

pub fn write_staging(path: &str, input_path: &str, snap: &StagingSnapshot) -> Result<(), String> {
    use std::fs;
    use std::path::Path;
    let payload = serde_json::json!({
        "input_path": input_path,
        "block_count": snap.block_count,
        "blocks": snap.blocks,
        "window_size": snap.window_size,
        "staging_adler": snap.staging_adler,
    });
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(path, serde_json::to_string_pretty(&payload).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())
}
