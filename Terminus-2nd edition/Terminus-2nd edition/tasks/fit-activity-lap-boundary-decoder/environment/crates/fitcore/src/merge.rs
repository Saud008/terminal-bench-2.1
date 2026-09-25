use crate::message::LapRow;

/// Legacy helper retained for compatibility with old callers.
/// The staging/export pipeline does not route through this module.
pub fn legacy_merge_rows(mut rows: Vec<LapRow>) -> Vec<LapRow> {
    rows.sort_by_key(|row| row.original_index);
    rows
}
