use crate::errors::BleveError;
use crate::state::fs::{load_meta, save_meta};
use std::path::Path;

pub fn allocate_doc_ids(root: &Path, count: usize) -> Result<Vec<u64>, BleveError> {
    let mut meta = load_meta(root)?;
    let start = meta.next_doc_id;

    meta.next_doc_id += count as u64;
    save_meta(root, &meta)?;

    let mut ids = Vec::with_capacity(count);
    for offset in 0..count {
        ids.push(start + offset as u64);
    }
    Ok(ids)
}
