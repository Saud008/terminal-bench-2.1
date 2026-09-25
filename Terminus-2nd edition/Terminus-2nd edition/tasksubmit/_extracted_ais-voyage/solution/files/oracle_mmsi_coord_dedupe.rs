use crate::maritime_types::{round6, AisRow, Policy};

pub fn dedupe_mmsi(rows: Vec<AisRow>, policy: Policy) -> (Vec<AisRow>, u64) {
    let mut kept: Vec<AisRow> = Vec::new();
    let mut removed = 0u64;
    'outer: for row in rows {
        for existing in &kept {
            if existing.mmsi != row.mmsi {
                continue;
            }
            if round6(existing.lat) != round6(row.lat) || round6(existing.lon) != round6(row.lon) {
                continue;
            }
            if (existing.ts_epoch - row.ts_epoch).abs() <= policy.mmsi_dedupe_sec {
                removed += 1;
                continue 'outer;
            }
        }
        kept.push(row);
    }
    (kept, removed)
}
