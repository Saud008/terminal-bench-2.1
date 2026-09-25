use crate::message::LapRow;

pub fn compute_staging_digest(rows: &[LapRow]) -> String {
    let mut acc: u64 = 1469598103934665603;
    for row in rows {
        acc ^= row.start_time as u64;
        acc = acc.wrapping_mul(1099511628211);
        acc ^= row.end_time as u64;
        acc = acc.wrapping_mul(1099511628211);
        acc ^= row.original_index as u64;
        acc = acc.wrapping_mul(1099511628211);
    }
    format!("{acc:016x}")
}
