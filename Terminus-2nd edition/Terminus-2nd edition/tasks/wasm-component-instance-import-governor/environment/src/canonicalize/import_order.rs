use crate::types::ImportRow;

/// Canonicalize import ordering for attestation.
pub fn canonical_imports(imports: &[ImportRow]) -> Vec<ImportRow> {
    let mut rows = imports.to_vec();
    rows.sort_by(|a, b| a.name.cmp(&b.name));
    rows
}
