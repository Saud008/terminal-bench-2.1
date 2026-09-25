use crate::layout::component_stride;
use crate::model::{ChunkEntity, LayoutManifest, CHUNK_MAGIC};
use anyhow::{Context, Result};
use std::fs;
use std::path::{Path, PathBuf};

pub fn chunk_path(dir: &Path, chunk_id: u32) -> PathBuf {
    dir.join(format!("chunk_{chunk_id:04}.bin"))
}

pub fn read_chunk(dir: &Path, chunk_id: u32) -> Result<(u32, Vec<ChunkEntity>)> {
    let bytes = fs::read(chunk_path(dir, chunk_id))
        .with_context(|| format!("read chunk {}", chunk_id))?;
    if bytes.len() < 16 {
        anyhow::bail!("chunk too small");
    }
    let magic = u32::from_be_bytes(bytes[0..4].try_into()?);
    if magic != CHUNK_MAGIC {
        anyhow::bail!("bad chunk magic");
    }
    let file_chunk_id = u32::from_be_bytes(bytes[4..8].try_into()?);
    let layout_version = u32::from_be_bytes(bytes[8..12].try_into()?);
    let payload_len = u32::from_be_bytes(bytes[12..16].try_into()?);
    let payload = &bytes[16..16 + payload_len as usize];
    let stride = component_stride_from_version(layout_version);
    let record = 4 + stride as usize;
    let mut entities = Vec::new();
    let mut off = 0usize;
    while off + record <= payload.len() {
        let stable_id = u32::from_be_bytes(payload[off..off + 4].try_into()?);
        let body = payload[off + 4..off + record].to_vec();
        entities.push(ChunkEntity {
            stable_id,
            payload: body,
        });
        off += record;
    }
    Ok((file_chunk_id, entities))
}

pub fn write_chunk(
    dir: &Path,
    chunk_id: u32,
    layout_version: u32,
    manifest: &LayoutManifest,
    entities: &[ChunkEntity],
) -> Result<()> {
    let stride = component_stride(manifest);
    let mut payload = Vec::new();
    for ent in entities {
        payload.extend_from_slice(&ent.stable_id.to_be_bytes());
        if ent.payload.len() < stride as usize {
            let mut padded = ent.payload.clone();
            padded.resize(stride as usize, 0);
            payload.extend_from_slice(&padded);
        } else {
            payload.extend_from_slice(&ent.payload[..stride as usize]);
        }
    }
    let mut out = Vec::new();
    out.extend_from_slice(&CHUNK_MAGIC.to_be_bytes());
    out.extend_from_slice(&chunk_id.to_be_bytes());
    out.extend_from_slice(&layout_version.to_be_bytes());
    out.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    out.extend_from_slice(&payload);
    fs::write(chunk_path(dir, chunk_id), out)?;
    Ok(())
}

pub fn list_chunk_ids(dir: &Path) -> Result<Vec<u32>> {
    let mut ids = Vec::new();
    if !dir.exists() {
        return Ok(ids);
    }
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().to_string();
        if let Some(rest) = name.strip_prefix("chunk_") {
            if let Some(id_str) = rest.strip_suffix(".bin") {
                if let Ok(id) = id_str.parse::<u32>() {
                    ids.push(id);
                }
            }
        }
    }
    ids.sort_unstable();
    Ok(ids)
}

fn component_stride_from_version(version: u32) -> u32 {
    if version >= 2 {
        14
    } else {
        12
    }
}
