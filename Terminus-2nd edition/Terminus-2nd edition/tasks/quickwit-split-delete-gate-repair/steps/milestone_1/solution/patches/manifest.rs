use crate::model::{Manifest, SplitEntry};
use std::fs;
use std::path::{Path, PathBuf};

pub fn manifest_path(state: &Path) -> PathBuf {
    state.join("manifest.json")
}

pub fn load_manifest(state: &Path) -> Result<Manifest, String> {
    let path = manifest_path(state);
    if !path.exists() {
        return Ok(Manifest {
            splits: Vec::new(),
            lineage_root: String::new(),
        });
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_manifest(state: &Path, manifest: &Manifest) -> Result<(), String> {
    let path = manifest_path(state);
    let raw = serde_json::to_string_pretty(manifest).map_err(|e| e.to_string())?;
    fs::write(path, raw).map_err(|e| e.to_string())
}

pub fn append_split(state: &Path, entry: SplitEntry) -> Result<(), String> {
    let mut manifest = load_manifest(state)?;
    if manifest.lineage_root.is_empty() {
        manifest.lineage_root = entry.split_id.clone();
    }
    manifest.splits.push(entry);
    save_manifest(state, &manifest)
}

pub fn append_merge_lineage(
    state: &Path,
    merged_id: &str,
    other_parent: &str,
    doc_count: i64,
    publish_seq: i64,
) -> Result<(), String> {
    append_split(
        state,
        SplitEntry {
            split_id: merged_id.to_string(),
            parent_split_id: Some(other_parent.to_string()),
            doc_count,
            publish_seq,
        },
    )
}
