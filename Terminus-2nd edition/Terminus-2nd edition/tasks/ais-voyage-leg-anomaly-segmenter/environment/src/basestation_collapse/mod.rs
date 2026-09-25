use crate::maritime_types::{AisRow, Policy};

pub fn collapse_bursts(rows: Vec<AisRow>, policy: Policy) -> (Vec<AisRow>, u64) {
    let mut kept: Vec<AisRow> = Vec::new();
    let mut removed = 0u64;
    for row in rows {
        let mut dup_idx: Option<usize> = None;
        for (i, existing) in kept.iter().enumerate() {
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
            dup_idx = Some(i);
            break;
        }
        if let Some(i) = dup_idx {
            removed += 1;
            if row.seq < kept[i].seq {
                kept[i] = row;
            }
        } else {
            kept.push(row);
        }
    }
    (kept, removed)
}
