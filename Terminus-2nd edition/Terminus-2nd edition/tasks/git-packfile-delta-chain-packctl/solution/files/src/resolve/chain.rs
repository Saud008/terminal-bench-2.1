use std::collections::HashMap;

use sha1::{Digest, Sha1};

use crate::inflate::{apply_patch, inflate_fresh};
use crate::resolve::ofs_base::ofs_copy_offset;
use crate::resolve::ref_base::lookup_ref_base;
use crate::types::{
    allowed_delta_base, PackStage, StageObject, KIND_BLOB, KIND_OFS_DELTA, KIND_REF_DELTA,
};

#[derive(Clone)]
pub struct ResolvedObject {
    pub id: String,
    pub kind: String,
    pub bytes: Vec<u8>,
    pub chain_depth: u32,
}

pub fn resolve_all(stage: &PackStage) -> Result<Vec<ResolvedObject>, String> {
    let order = base_first_order(&stage.objects);
    let mut by_id: HashMap<String, ResolvedObject> = HashMap::new();
    let mut out = Vec::new();

    for idx in order {
        let obj = &stage.objects[idx];
        if obj.kind == KIND_REF_DELTA {
            if let Some(base_id) = &obj.base_id {
                if let Some(base) = stage.objects.iter().find(|o| o.id == *base_id) {
                    if !allowed_delta_base(&base.kind) {
                        continue;
                    }
                }
            }
        }
        let resolved = resolve_one(stage, obj, &by_id)?;
        by_id.insert(obj.id.clone(), resolved.clone());
        out.push(resolved);
    }
    out.sort_by_key(|o| o.id.clone());
    Ok(out)
}

fn base_first_order(objects: &[StageObject]) -> Vec<usize> {
    let mut depths = vec![0u32; objects.len()];
    for _ in 0..objects.len() {
        for (i, obj) in objects.iter().enumerate() {
            if let Some(base_id) = &obj.base_id {
                if let Some(j) = objects.iter().position(|o| o.id == *base_id) {
                    depths[i] = depths[i].max(depths[j] + 1);
                }
            } else if obj.kind == KIND_OFS_DELTA {
                if let Some(off) = obj.base_pack_offset {
                    if let Some(j) = objects.iter().position(|o| o.pack_offset == off) {
                        depths[i] = depths[i].max(depths[j] + 1);
                    }
                }
            }
        }
    }
    let mut order: Vec<usize> = (0..objects.len()).collect();
    order.sort_by_key(|&i| (depths[i], objects[i].catalog_order));
    order
}

fn resolve_one(
    stage: &PackStage,
    obj: &StageObject,
    cache: &HashMap<String, ResolvedObject>,
) -> Result<ResolvedObject, String> {
    match obj.kind.as_str() {
        KIND_BLOB | "tree" | "commit" => {
            let raw = inflate_fresh(&stage.pack_stream_path, obj.pack_offset, obj.compressed_size)?;
            Ok(ResolvedObject {
                id: obj.id.clone(),
                kind: obj.kind.clone(),
                bytes: raw,
                chain_depth: 0,
            })
        }
        KIND_REF_DELTA => {
            let base_id = obj.base_id.as_ref().ok_or("ref_delta missing base_id")?;
            lookup_ref_base(stage, base_id)?;
            let base_resolved = cache
                .get(base_id)
                .ok_or("ref base not resolved yet")?;
            let patch_raw =
                inflate_fresh(&stage.pack_stream_path, obj.pack_offset, obj.compressed_size)?;
            let bytes = apply_patch(&base_resolved.bytes, &patch_raw)?;
            Ok(ResolvedObject {
                id: obj.id.clone(),
                kind: obj.kind.clone(),
                bytes,
                chain_depth: base_resolved.chain_depth + 1,
            })
        }
        KIND_OFS_DELTA => {
            let base_off = obj.base_pack_offset.ok_or("ofs_delta missing base_pack_offset")?;
            let base_obj = stage
                .objects
                .iter()
                .find(|o| o.pack_offset == base_off)
                .ok_or("ofs base not found")?;
            let base_resolved = cache
                .get(&base_obj.id)
                .ok_or("ofs base not resolved yet")?;
            let patch_raw =
                inflate_fresh(&stage.pack_stream_path, obj.pack_offset, obj.compressed_size)?;
            let copy_off = ofs_copy_offset();
            let window = &base_resolved.bytes[copy_off..];
            let bytes = apply_patch(window, &patch_raw)?;
            Ok(ResolvedObject {
                id: obj.id.clone(),
                kind: obj.kind.clone(),
                bytes,
                chain_depth: base_resolved.chain_depth + 1,
            })
        }
        other => Err(format!("unsupported kind {other}")),
    }
}

pub fn object_sha1(bytes: &[u8]) -> String {
    let mut hasher = Sha1::new();
    hasher.update(bytes);
    hex::encode(hasher.finalize())
}
