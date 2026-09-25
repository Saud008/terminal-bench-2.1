use crate::maritime_types::{AisRow, Policy};

pub fn collapse_bursts(rows: Vec<AisRow>, policy: Policy) -> (Vec<AisRow>, u64) {
    let mut kept: Vec<AisRow> = Vec::new();
    let mut removed = 0u64;
    'outer: for row in rows {
        for existing in &kept {
            if existing.mmsi != row.mmsi || existing.station != row.station {
                continue;
            }
            let dt_ms = (existing.ts_epoch - row.ts_epoch).abs() * 1000;
            if dt_ms > policy.burst_ms {
                continue;
            }
            if (existing.lat - row.lat).abs() > 0.0001 || (existing.lon - row.lon).abs() > 0.0001 {
                continue;
            }
            removed += 1;
            continue 'outer;
        }
        kept.push(row);
    }
    (kept, removed)
}
