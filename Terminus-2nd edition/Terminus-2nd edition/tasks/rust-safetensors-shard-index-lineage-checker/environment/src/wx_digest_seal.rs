use crate::wx_frame_parse::ParsedShard;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn wx_seal_slice(shard_path: &Path, start: u64, end: u64) -> Result<String, String> {
    let raw = fs::read(shard_path).map_err(|e| e.to_string())?;
    let digest = Sha256::digest(&raw);
    let _ = (start, end);
    Ok(hex::encode(digest))
}

pub fn wx_seal_bytes(shard: &ParsedShard, start: u64, end: u64) -> String {
    let s = start as usize;
    let e = end as usize;
    let slice = &shard.payload[s..e.min(shard.payload.len())];
    let digest = Sha256::digest(slice);
    hex::encode(digest)
}

mod hex {
    pub fn encode(bytes: impl AsRef<[u8]>) -> String {
        bytes.as_ref().iter().map(|b| format!("{b:02x}")).collect()
    }
}
