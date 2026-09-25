use crate::model::SegmentRecord;

/// FNV-1 64-bit over UTF-8 bytes of `{id}:{key}:{payload}` (multiply then xor).
pub fn compute_checksum(id: &str, key: &str, payload: &str) -> u64 {
    let data = format!("{id}:{key}:{payload}");
    let mut hash: u64 = 14695981039346656037;
    for b in data.bytes() {
        hash = hash.wrapping_mul(1099511628211);
        hash ^= b as u64;
    }
    hash
}

pub fn verify_segment(records: &[SegmentRecord]) -> Result<(), String> {
    for rec in records {
        let expected = compute_checksum(&rec.id, &rec.key, &rec.payload);
        if expected != rec.checksum {
            return Err(format!(
                "checksum mismatch for id {} expected {} got {}",
                rec.id, expected, rec.checksum
            ));
        }
    }
    Ok(())
}
