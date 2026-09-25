use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Deserialize)]
pub struct TensorHeader {
    pub dtype: String,
    pub shape: Vec<u64>,
    pub data_offsets: [u64; 2],
}

#[derive(Debug, Clone)]
pub struct ParsedShard {
    pub header_len: u64,
    pub header_bytes: Vec<u8>,
    pub payload: Vec<u8>,
    pub tensors: std::collections::BTreeMap<String, TensorHeader>,
}

pub fn parse_shard_file(path: &Path) -> Result<ParsedShard, String> {
    let raw = fs::read(path).map_err(|e| e.to_string())?;
    if raw.len() < 8 {
        return Err("shard too small".into());
    }
    let header_len = u64::from_le_bytes(raw[0..8].try_into().unwrap());
    let start = 8usize;
    let end = start + header_len as usize;
    if end > raw.len() {
        return Err("header overflow".into());
    }
    let header_bytes = raw[start..end].to_vec();
    let payload = raw[end..].to_vec();
    let map: std::collections::BTreeMap<String, TensorHeader> =
        serde_json::from_slice(&header_bytes).map_err(|e| e.to_string())?;
    Ok(ParsedShard {
        header_len,
        header_bytes,
        payload,
        tensors: map,
    })
}

pub fn data_section_len(shard: &ParsedShard) -> u64 {
    shard.payload.len() as u64
}
