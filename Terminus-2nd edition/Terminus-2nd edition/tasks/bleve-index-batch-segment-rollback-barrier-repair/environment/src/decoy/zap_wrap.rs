use crate::model::SegmentRecord;

/// Legacy zap wrap helper (not on the ingest/export hot path).
/// Uses FNV-1a over id/key/payload — do not treat this as the segment checksum contract.
#[allow(dead_code)]
pub fn wrap_records(records: &[SegmentRecord]) -> Vec<String> {
    records
        .iter()
        .map(|r| format!("{}::{}::{:#x}", r.id, r.key, fnv1a_legacy(&r.id, &r.key, &r.payload)))
        .collect()
}

#[allow(dead_code)]
fn fnv1a_legacy(id: &str, key: &str, payload: &str) -> u64 {
    let data = format!("{id}:{key}:{payload}");
    let mut hash: u64 = 14695981039346656037;
    for b in data.bytes() {
        hash ^= b as u64;
        hash = hash.wrapping_mul(1099511628211);
    }
    hash
}
