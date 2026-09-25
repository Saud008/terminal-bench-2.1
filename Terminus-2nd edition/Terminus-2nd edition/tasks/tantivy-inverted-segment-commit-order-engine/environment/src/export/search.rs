use crate::segment::{load_segment, search_term};
use crate::staging::load_catalog;
use std::fs;
use std::path::Path;

pub fn search_index(index: &str, field: &str, term: &str, out: &Path) -> Result<(), String> {
    let cat = load_catalog()?;
    let state = cat
        .indexes
        .get(index)
        .ok_or_else(|| format!("index {index} missing"))?;

    let seg_ids = &state.staging_segment_ids;
    let mut hits: Vec<u32> = Vec::new();
    for id in seg_ids {
        let seg = load_segment(index, id)?;
        hits.extend(search_term(&seg, field, term));
    }
    hits.sort_unstable();
    hits.dedup();

    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir out: {e}"))?;
    }
    fs::write(out, serde_json::to_string_pretty(&hits).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write search out: {e}"))?;
    Ok(())
}
