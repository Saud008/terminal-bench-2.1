pub mod batch;
pub mod replay;

use crate::ingest::replay::collapse_puts;
use crate::ingest::batch::{parse_batch_file, BatchOp};
use crate::staging::{apply_puts, load_staging, save_staging};
use std::path::Path;

pub fn apply_batch_file(table: &str, input: &Path) -> Result<(), String> {
    let ops = parse_batch_file(input)?;
    let puts = collapse_puts(&ops);
    apply_puts(table, &puts)?;
    let mut state = load_staging()?;
    let tree = state.tables.get_or_insert(table);
    for op in ops {
        if let BatchOp::Delete { key } = op {
            crate::btree::delete(tree, &key)?;
        }
    }
    save_staging(&state)
}
