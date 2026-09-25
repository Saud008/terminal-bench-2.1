use crate::cache::HotCache;
use crate::checkpoint::record_merge_attempt;
use crate::manifest::{append_merge_lineage, load_manifest};
use crate::model::{MergeAudit, SplitMeta};
use crate::store::{docs_for_split, open_db, reassign_split};
use std::fs;
use std::path::Path;

fn split_meta_path(state: &Path) -> std::path::PathBuf {
    state.join("split-meta.json")
}

pub fn load_split_meta(state: &Path) -> Result<SplitMeta, String> {
    let path = split_meta_path(state);
    if !path.exists() {
        return Ok(SplitMeta {
            active_splits: Vec::new(),
            publish_seq: 0,
        });
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_split_meta(state: &Path, meta: &SplitMeta) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(meta).map_err(|e| e.to_string())?;
    fs::write(split_meta_path(state), raw).map_err(|e| e.to_string())
}

pub fn run_merge(
    state: &Path,
    db: &Path,
    left: &str,
    right: &str,
) -> Result<MergeAudit, String> {
    let meta = load_split_meta(state)?;
    if !meta.active_splits.contains(&left.to_string())
        || !meta.active_splits.contains(&right.to_string())
    {
        record_merge_attempt(state, false)?;
        return Err("unknown split".into());
    }

    let conn = open_db(db).map_err(|e| e.to_string())?;
    let left_docs = docs_for_split(&conn, left).map_err(|e| e.to_string())?;
    let right_docs = docs_for_split(&conn, right).map_err(|e| e.to_string())?;

    let merged_id = if left < right {
        left.to_string()
    } else {
        right.to_string()
    };
    let other = if merged_id == left {
        right.to_string()
    } else {
        left.to_string()
    };

    reassign_split(&conn, &other, &merged_id).map_err(|e| e.to_string())?;

    let mut cache = HotCache::new();
    cache.load_split(left, left_docs.clone());
    cache.load_split(right, right_docs.clone());

    let mut new_meta = meta.clone();
    new_meta.active_splits.retain(|s| s != left && s != right);
    new_meta.active_splits.push(merged_id.clone());
    new_meta.publish_seq += 1;
    save_split_meta(state, &new_meta)?;

    cache.drop_metadata_only(left);
    cache.drop_metadata_only(right);

    let cache_flushed = cache.get(left).is_none() && cache.get(right).is_none();

    let manifest = load_manifest(state)?;
    let publish_seq = manifest.splits.len() as i64 + 1;
    append_merge_lineage(
        state,
        &merged_id,
        &other,
        (left_docs.len() + right_docs.len()) as i64,
        publish_seq,
    )?;

    let audit = MergeAudit {
        status: "complete".into(),
        merged_into: merged_id,
        sources: vec![left.to_string(), right.to_string()],
        cache_flushed,
    };

    let audit_path = state.join("merge-audit.json");
    fs::write(
        &audit_path,
        serde_json::to_string_pretty(&audit).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    record_merge_attempt(state, true)?;
    Ok(audit)
}
