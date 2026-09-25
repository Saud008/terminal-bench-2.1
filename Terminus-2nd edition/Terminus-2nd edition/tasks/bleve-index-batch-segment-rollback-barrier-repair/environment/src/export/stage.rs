use crate::collator::key_order::{load_collator, sort_keys};
use crate::errors::BleveError;
use crate::model::ExportManifest;
use crate::segment::store::read_segment;
use crate::state::fs::{ensure_index_dirs, load_root_map};
use std::fs;
use std::path::Path;

pub fn export_index(index: &str, output_path: &Path) -> Result<(), BleveError> {
    let root = ensure_index_dirs(index)?;
    let map = load_root_map(&root)?;
    let collator = load_collator()?;

    let mut keys = Vec::new();
    let mut doc_count = 0usize;
    for segment_file in &map.segments {
        let seg = read_segment(&root, segment_file)?;
        doc_count += seg.records.len();
        for rec in seg.records {
            keys.push(rec.key);
        }
    }
    sort_keys(&collator, &mut keys);

    let manifest = ExportManifest {
        index: index.to_string(),
        doc_count,
        segments: map.segments,
        ordered_keys: keys,
    };

    fs::write(
        output_path,
        format!("{}\n", serde_json::to_string_pretty(&manifest)?),
    )?;
    Ok(())
}
