use crate::types::ImportRow;

/// Canonicalize import ordering for attestation per import-tuple-rank.md.
pub fn canonical_imports(imports: &[ImportRow]) -> Vec<ImportRow> {
    let mut rows = imports.to_vec();
    rows.sort_by(|a, b| {
        let ma = a.module.as_bytes();
        let mb = b.module.as_bytes();
        ma.cmp(mb).then_with(|| a.name.as_bytes().cmp(b.name.as_bytes()))
    });
    rows
}
