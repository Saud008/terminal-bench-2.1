pub mod gaps;
pub mod padding;

use crate::types::LedgerFile;

pub fn relayout_from_ledger(ledger: &LedgerFile) -> Result<Vec<u8>, String> {
    if ledger.entries.is_empty() {
        return Err("ledger has no wire entries".into());
    }
    let entry = &ledger.entries[0];
    let mut out = gaps::compact_without_gaps(&entry.wire, &entry.gaps);
    padding::apply_padding_before_fixup(&mut out, entry)?;
    gaps::restore_gaps(&mut out, entry)?;
    Ok(out)
}
