use crate::field_schema::{QuotaLedgerRow, QuotaWindow};
use std::collections::BTreeMap;

pub fn build_quota_ledger(
    windows: &[QuotaWindow],
    usage_m3: &BTreeMap<u32, f64>,
) -> Vec<QuotaLedgerRow> {
    let mut rows = Vec::new();
    let mut carry = 0.0;
    for w in windows {
        let used = usage_m3.get(&w.window_index).copied().unwrap_or(0.0);
        let available = w.max_m3 + carry;
        let leftover = (available - used).max(0.0);
        let carry_out = leftover.min(w.max_carry_m3);
        rows.push(QuotaLedgerRow {
            window_index: w.window_index,
            base_m3: w.max_m3,
            carry_in_m3: carry,
            used_m3: used,
            carry_out_m3: carry_out,
        });
        carry = carry_out;
    }
    rows.sort_by_key(|r| r.window_index);
    rows
}
