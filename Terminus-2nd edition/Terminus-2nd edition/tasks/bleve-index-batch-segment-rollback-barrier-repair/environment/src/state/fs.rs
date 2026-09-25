use crate::errors::BleveError;
use crate::model::{BatchSnapshot, IndexMeta, RootMap};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

pub fn index_root(index: &str) -> PathBuf {
    let prefix = env::var("TB3_INDEX_PREFIX").unwrap_or_else(|_| "/app/state/indexes".to_string());
    Path::new(&prefix).join(index)
}

pub fn ensure_index_dirs(index: &str) -> Result<PathBuf, BleveError> {
    let root = index_root(index);
    fs::create_dir_all(root.join("segments"))?;
    Ok(root)
}

pub fn root_map_path(root: &Path) -> PathBuf {
    root.join("root-map.json")
}

pub fn index_meta_path(root: &Path) -> PathBuf {
    root.join("meta.json")
}

pub fn open_batch_path(root: &Path) -> PathBuf {
    root.join("open-batch.flag")
}

pub fn load_root_map(root: &Path) -> Result<RootMap, BleveError> {
    let path = root_map_path(root);
    if !path.exists() {
        return Ok(RootMap::default());
    }
    Ok(serde_json::from_str(&fs::read_to_string(path)?)?)
}

pub fn save_root_map(root: &Path, map: &RootMap) -> Result<(), BleveError> {
    fs::write(root_map_path(root), format!("{}\n", serde_json::to_string_pretty(map)?))?;
    Ok(())
}

pub fn load_meta(root: &Path) -> Result<IndexMeta, BleveError> {
    let path = index_meta_path(root);
    if !path.exists() {
        return Ok(IndexMeta { next_doc_id: 1 });
    }
    Ok(serde_json::from_str(&fs::read_to_string(path)?)?)
}

pub fn save_meta(root: &Path, meta: &IndexMeta) -> Result<(), BleveError> {
    fs::write(
        index_meta_path(root),
        format!("{}\n", serde_json::to_string_pretty(meta)?),
    )?;
    Ok(())
}

pub fn set_open_batch(root: &Path, open: bool) -> Result<(), BleveError> {
    let path = open_batch_path(root);
    if open {
        fs::write(path, "open\n")?;
    } else if path.exists() {
        fs::remove_file(path)?;
    }
    Ok(())
}

pub fn write_snapshot(snapshot: &BatchSnapshot) -> Result<(), BleveError> {
    let path = Path::new("/app/state/batch-snapshot.json");
    fs::create_dir_all("/app/state")?;
    fs::write(path, format!("{}\n", serde_json::to_string_pretty(snapshot)?))?;
    Ok(())
}
