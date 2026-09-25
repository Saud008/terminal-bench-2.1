use crate::message::PickRow;

pub fn compute_staging_digest(picks: &[PickRow], effective_polarity: i8) -> String {
    let mut rows: Vec<&PickRow> = picks.iter().collect();
    rows.sort_by_key(|row| row.phase_code);
    let mut acc: u64 = 1469598103934665603;
    for row in rows {
        acc ^= row.sample_idx as u64;
        acc = acc.wrapping_mul(1099511628211);
        acc ^= row.phase_code as u64;
        acc = acc.wrapping_mul(1099511628211);
        acc ^= (effective_polarity as u8) as u64;
        acc = acc.wrapping_mul(1099511628211);
    }
    format!("{acc:016x}")
}
