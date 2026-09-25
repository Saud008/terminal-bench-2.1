use crate::mw11::{QuotaLedgerRow, RegionSpec};
use std::collections::BTreeMap;

pub fn build_quota_ledger(
    regions: &BTreeMap<String, RegionSpec>,
    window_count: u32,
    usage: &BTreeMap<(String, u32), u32>,
) -> Vec<QuotaLedgerRow> {
    let mut rows = Vec::new();
    for (region, spec) in regions {
        for w in 0..window_count {
            let used = usage.get(&(region.clone(), w)).copied().unwrap_or(0);
            rows.push(QuotaLedgerRow {
                region: region.clone(),
                window_index: w,
                base_quota: spec.quota_per_window,
                carry_in: 0,
                used,
                carry_out: 0,
            });
        }
    }
    rows.sort_by(|a, b| (a.region.clone(), a.window_index).cmp(&(b.region.clone(), b.window_index)));
    rows
}

pub fn available_quota(row: &QuotaLedgerRow) -> u32 {
    row.base_quota + row.carry_in
}
