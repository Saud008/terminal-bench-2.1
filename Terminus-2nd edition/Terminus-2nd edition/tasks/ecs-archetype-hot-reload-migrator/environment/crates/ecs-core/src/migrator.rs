use crate::chunk_store::{read_chunk, write_chunk};
use crate::layout::component_stride;
use crate::model::{ChunkEntity, LayoutManifest, MigrationStep};
use anyhow::Result;
use rusqlite::{Connection, params};
use std::collections::HashMap;
use std::path::Path;

pub fn ordered_steps(manifest: &LayoutManifest) -> Vec<MigrationStep> {
    let mut steps = manifest.migration_steps.clone();
    steps.sort_by(|a, b| a.component.cmp(&b.component));
    steps
}

pub fn apply_steps(
    conn: &Connection,
    chunks_dir: &Path,
    manifest: &LayoutManifest,
    start_from: u32,
) -> Result<(Vec<(u32, String, String, u32)>, u32)> {
    let steps = ordered_steps(manifest);
    let mut applied = Vec::new();
    let mut moved = 0u32;
    let stride_v2 = component_stride(manifest) as usize;
    for step in steps.iter().filter(|s| s.order > start_from) {
        let mut touched: HashMap<u32, u32> = HashMap::new();
        let chunk_ids = crate::chunk_store::list_chunk_ids(chunks_dir)?;
        for chunk_id in chunk_ids {
            if step.op == "move" {
                if let Some(target) = step.target_chunk {
                    if chunk_id == target {
                        continue;
                    }
                }
            }
            let (_id, mut entities) = read_chunk(chunks_dir, chunk_id)?;
            let mut changed = false;
            match step.op.as_str() {
                "add" => {
                    if let Some(comp) = manifest.components.iter().find(|c| c.name == step.component) {
                        for ent in entities.iter_mut() {
                            let mut body = ent.payload.clone();
                            body.resize(stride_v2, 0);
                            if let Some(hex) = &comp.default_hex {
                                let bytes = hex::decode(hex.trim_start_matches("0x"))?;
                                let start = comp.offset as usize;
                                for (i, b) in bytes.iter().enumerate() {
                                    if start + i < body.len() {
                                        body[start + i] = *b;
                                    }
                                }
                            }
                            ent.payload = body;
                            changed = true;
                        }
                    }
                }
                "move" => {
                    if let (Some(target), Some(from_sig)) =
                        (step.target_chunk, step.from_archetype.as_ref())
                    {
                        let keep: Vec<ChunkEntity> = entities
                            .iter()
                            .filter(|e| {
                                let sig = crate::layout::signature_for_payload(manifest, &e.payload);
                                sig != *from_sig
                            })
                            .cloned()
                            .collect();
                        let moving: Vec<ChunkEntity> = entities
                            .iter()
                            .filter(|e| {
                                let sig = crate::layout::signature_for_payload(manifest, &e.payload);
                                sig == *from_sig
                            })
                            .cloned()
                            .collect();
                        if !moving.is_empty() {
                            let (_, mut target_ents) = read_chunk(chunks_dir, target)?;
                            target_ents.extend(moving.clone());
                            write_chunk(
                                chunks_dir,
                                target,
                                manifest.to_version,
                                manifest,
                                &target_ents,
                            )?;
                            write_chunk(
                                chunks_dir,
                                chunk_id,
                                manifest.to_version,
                                manifest,
                                &keep,
                            )?;
                            for ent in &moving {
                                conn.execute(
                                    "UPDATE entities SET chunk_id = ?1 WHERE stable_id = ?2",
                                    params![target as i64, ent.stable_id as i64],
                                )?;
                            }
                            moved += moving.len() as u32;
                            changed = true;
                            entities = keep;
                        }
                    }
                }
                _ => {}
            }
            if changed {
                *touched.entry(chunk_id).or_insert(0) += 1;
                if step.op != "move" {
                    write_chunk(
                        chunks_dir,
                        chunk_id,
                        manifest.to_version,
                        manifest,
                        &entities,
                    )?;
                }
            }
        }
        let chunks_touched = touched.len() as u32;
        applied.push((step.order, step.op.clone(), step.component.clone(), chunks_touched));
    }
    Ok((applied, moved))
}

mod hex {
    pub fn decode(s: &str) -> anyhow::Result<Vec<u8>> {
        if s.len() % 2 != 0 {
            anyhow::bail!("odd hex");
        }
        let mut out = Vec::new();
        let bytes = s.as_bytes();
        let mut i = 0;
        while i < bytes.len() {
            let hi = from_hex(bytes[i])?;
            let lo = from_hex(bytes[i + 1])?;
            out.push((hi << 4) | lo);
            i += 2;
        }
        Ok(out)
    }
    fn from_hex(b: u8) -> anyhow::Result<u8> {
        Ok(match b {
            b'0'..=b'9' => b - b'0',
            b'a'..=b'f' => b - b'a' + 10,
            b'A'..=b'F' => b - b'A' + 10,
            _ => anyhow::bail!("bad hex"),
        })
    }
}
