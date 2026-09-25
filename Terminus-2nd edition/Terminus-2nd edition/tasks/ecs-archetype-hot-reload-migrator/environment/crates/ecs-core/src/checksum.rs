use crate::model::CHUNK_MAGIC;
use sha2::{Digest, Sha256};

pub fn chunk_checksum(chunk_id: u32, layout_version: u32, payload: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(CHUNK_MAGIC.to_le_bytes());
    hasher.update(chunk_id.to_le_bytes());
    hasher.update(layout_version.to_le_bytes());
    hasher.update((payload.len() as u32).to_le_bytes());
    hasher.update(payload);
    format!("{:x}", hasher.finalize())
}

pub fn decode_chunk(bytes: &[u8]) -> anyhow::Result<(u32, u32, Vec<u8>)> {
    if bytes.len() < 16 {
        anyhow::bail!("chunk too small");
    }
    let magic = u32::from_be_bytes(bytes[0..4].try_into()?);
    if magic != CHUNK_MAGIC {
        anyhow::bail!("bad chunk magic");
    }
    let chunk_id = u32::from_be_bytes(bytes[4..8].try_into()?);
    let layout_version = u32::from_be_bytes(bytes[8..12].try_into()?);
    let payload_len = u32::from_be_bytes(bytes[12..16].try_into()?);
    let end = 16 + payload_len as usize;
    if bytes.len() < end {
        anyhow::bail!("truncated chunk payload");
    }
    Ok((chunk_id, layout_version, bytes[16..end].to_vec()))
}
