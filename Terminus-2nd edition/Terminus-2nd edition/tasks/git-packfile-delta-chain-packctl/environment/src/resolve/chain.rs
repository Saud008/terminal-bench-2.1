use std::collections::HashMap;

use sha1::{Digest, Sha1};

use crate::inflate::{apply_patch, inflate_at};
use crate::resolve::ofs_base::ofs_copy_offset;
use crate::resolve::ref_base::lookup_ref_base;
use crate::types::{
    PackStage, StageObject, KIND_BLOB, KIND_OFS_DELTA, KIND_REF_DELTA,
};

#[derive(Clone)]
pub struct ResolvedObject {
    pub id: String,
    pub kind: String,
    pub bytes: Vec<u8>,
    pub chain_depth: u32,
}

pub fn resolve_all(stage: &PackStage) -> Result<Vec<ResolvedObject>, String> {
    let order = depth_first_order(&stage.objects);
    let mut by_id: HashMap<String, ResolvedObject> = HashMap::new();
    let mut out = Vec::new();

    for idx in order {
        let obj = &stage.objects[idx];
        let resolved = resolve_one(stage, obj, &by_id)?;
        by_id.insert(obj.id.clone(), resolved.clone());
        out.push(resolved);
    }
    out.sort_by_key(|o| o.id.clone());
    Ok(out)
}

fn depth_first_order(objects: &[StageObject]) -> Vec<usize> {
    let mut order = Vec::new();
    let mut seen = vec![false; objects.len()];
    for i in 0..objects.len() {
        dfs(i, objects, &mut seen, &mut order);
    }
    order
}

fn dfs(i: usize, objects: &[StageObject], seen: &mut [bool], order: &mut Vec<usize>) {
    if seen[i] {
        return;
    }
    seen[i] = true;
    order.push(i);
    if let Some(base_id) = &objects[i].base_id {
        if let Some(j) = objects.iter().position(|o| o.id == *base_id) {
            dfs(j, objects, seen, order);
        }
    }
}

fn resolve_one(
    stage: &PackStage,
    obj: &StageObject,
    cache: &HashMap<String, ResolvedObject>,
) -> Result<ResolvedObject, String> {
    match obj.kind.as_str() {
        KIND_BLOB | "tree" | "commit" => {
            let raw = inflate_at(&stage.pack_stream_path, obj.pack_offset, obj.compressed_size)?;
            Ok(ResolvedObject {
                id: obj.id.clone(),
                kind: obj.kind.clone(),
                bytes: raw,
                chain_depth: 0,
            })
        }
        KIND_REF_DELTA => {
            let base_id = obj.base_id.as_ref().ok_or("ref_delta missing base_id")?;
            let _base_obj = lookup_ref_base(stage, base_id)?;
            let patch_raw = inflate_at(&stage.pack_stream_path, obj.pack_offset, obj.compressed_size)?;
            let base_bytes = cache
                .get(base_id)
                .map(|r| r.bytes.as_slice())
                .unwrap_or(&[]);
            let bytes = apply_patch(base_bytes, &patch_raw)?;
            let depth = cache.get(base_id).map(|b| b.chain_depth + 1).unwrap_or(1);
            Ok(ResolvedObject {
                id: obj.id.clone(),
                kind: obj.kind.clone(),
                bytes,
                chain_depth: depth,
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
            let patch_raw = inflate_at(&stage.pack_stream_path, obj.pack_offset, obj.compressed_size)?;
            let copy_off = ofs_copy_offset(base_resolved.bytes.len(), patch_raw.len());
            let mut synthetic_base = base_resolved.bytes.clone();
            if copy_off < synthetic_base.len() {
                synthetic_base = synthetic_base[copy_off..].to_vec();
            }
            let bytes = apply_patch(&synthetic_base, &patch_raw)?;
            let depth = base_resolved.chain_depth + 1;
            Ok(ResolvedObject {
                id: obj.id.clone(),
                kind: obj.kind.clone(),
                bytes,
                chain_depth: depth,
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
