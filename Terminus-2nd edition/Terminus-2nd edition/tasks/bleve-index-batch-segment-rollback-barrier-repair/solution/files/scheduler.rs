use crate::errors::BleveError;
use crate::state::fs::load_root_map;
use std::fs;
use std::path::Path;

pub fn maybe_schedule_merge(root: &Path, open_batch: bool, segment_count: usize) -> Result<(), BleveError> {
    let disk_open = root.join("open-batch.flag").exists();
    if open_batch || disk_open {
        return Ok(());
    }
    let map = load_root_map(root)?;
    let count = map.segments.len();
    if count < 2 || segment_count < 2 {
        return Ok(());
    }
    let plan = root.join("merge-plan.json");
    let body = serde_json::json!({
        "scheduled": true,
        "open_batch": false,
        "segment_count": count,
        "segments": map.segments,
    });
    fs::write(plan, format!("{}\n", serde_json::to_string(&body)?))?;
    Ok(())
}
