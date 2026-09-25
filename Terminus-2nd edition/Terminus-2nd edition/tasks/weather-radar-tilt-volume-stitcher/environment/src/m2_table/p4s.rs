use std::collections::BTreeMap;

pub fn apply_offset(raw_dbz: f64, channel: &str, table: &BTreeMap<String, f64>) -> f64 {
    let offset = table.get(channel).copied().unwrap_or(0.0);
    ((raw_dbz - offset) * 100.0).round() / 100.0
}
