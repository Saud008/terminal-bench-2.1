pub mod batch;
pub mod replay;

use crate::ingest::batch::{parse_batch_file, BatchOp};
use crate::ingest::replay::collapse_puts;
use crate::staging::{apply_puts, load_staging, save_staging};
use std::collections::BTreeMap;
use std::path::Path;

pub fn apply_batch_file(table: &str, input: &Path) -> Result<(), String> {
    let ops = parse_batch_file(input)?;
    let puts = collapse_puts(&ops);
    apply_puts(table, &puts)?;
    let mut state = load_staging()?;
    let tree = state.tables.get_or_insert(table);
    // Only keys whose final op is delete are removed; a later put after delete wins.
    let mut final_is_delete: BTreeMap<String, bool> = BTreeMap::new();
    for op in &ops {
        match op {
            BatchOp::Put { key, .. } => {
                final_is_delete.insert(key.clone(), false);
            }
            BatchOp::Delete { key } => {
                final_is_delete.insert(key.clone(), true);
            }
        }
    }
    for (key, should_delete) in final_is_delete {
        if should_delete {
            crate::btree::delete(tree, &key)?;
        }
    }
    save_staging(&state)
}
