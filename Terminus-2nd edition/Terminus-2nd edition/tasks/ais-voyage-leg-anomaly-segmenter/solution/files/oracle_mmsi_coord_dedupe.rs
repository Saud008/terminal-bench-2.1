use crate::maritime_types::{round6, AisRow, Policy};

pub fn dedupe_mmsi(rows: Vec<AisRow>, policy: Policy) -> (Vec<AisRow>, u64) {
    let mut kept: Vec<AisRow> = Vec::new();
    let mut removed = 0u64;
    for row in rows {
        let mut dup_idx: Option<usize> = None;
        for (i, existing) in kept.iter().enumerate() {
            if existing.mmsi != row.mmsi {
                continue;
            }
            if round6(existing.lat) != round6(row.lat) || round6(existing.lon) != round6(row.lon) {
                continue;
            }
            if (existing.ts_epoch - row.ts_epoch).abs() <= policy.mmsi_dedupe_sec {
                dup_idx = Some(i);
                break;
            }
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
