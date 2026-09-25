use crate::mw11::{QuotaLedgerRow, RegionSpec};
use std::collections::BTreeMap;

pub fn build_quota_ledger(
    regions: &BTreeMap<String, RegionSpec>,
    window_count: u32,
    usage: &BTreeMap<(String, u32), u32>,
) -> Vec<QuotaLedgerRow> {
    let mut rows = Vec::new();
    for (region, spec) in regions {
        let mut carry_in = 0u32;
        for w in 0..window_count {
            let used = usage.get(&(region.clone(), w)).copied().unwrap_or(0);
            let available = spec.quota_per_window + carry_in;
            let leftover = available.saturating_sub(used);
            let carry_out = leftover.min(spec.max_carryover);
            rows.push(QuotaLedgerRow {
                region: region.clone(),
                window_index: w,
                base_quota: spec.quota_per_window,
                carry_in,
                used,
                carry_out,
            });
            carry_in = carry_out;
        }
    }
    rows.sort_by(|a, b| (a.region.clone(), a.window_index).cmp(&(b.region.clone(), b.window_index)));
    rows
}
