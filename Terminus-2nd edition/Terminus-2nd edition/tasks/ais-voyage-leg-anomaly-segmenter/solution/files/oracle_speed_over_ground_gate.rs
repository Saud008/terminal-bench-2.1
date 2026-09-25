use crate::maritime_types::{AisRow, Policy};

const EARTH_RADIUS_NM: f64 = 3440.065;

pub fn haversine_nm(a: &AisRow, b: &AisRow) -> f64 {
    let lat1 = a.lat.to_radians();
    let lat2 = b.lat.to_radians();
    let dlat = (b.lat - a.lat).to_radians();
    let dlon = (b.lon - a.lon).to_radians();
    let h = (dlat / 2.0).sin().powi(2) + lat1.cos() * lat2.cos() * (dlon / 2.0).sin().powi(2);
    2.0 * EARTH_RADIUS_NM * h.sqrt().asin()
}

pub fn suppress_impossible_speed(rows: Vec<AisRow>, policy: Policy) -> (Vec<AisRow>, u64) {
    let mut by_mmsi: std::collections::BTreeMap<u64, Vec<AisRow>> = std::collections::BTreeMap::new();
    for row in rows {
        by_mmsi.entry(row.mmsi).or_default().push(row);
    }
    let mut kept_all = Vec::new();
    let mut removed = 0u64;
    for (_mmsi, mut track) in by_mmsi {
        track.sort_by(|a, b| a.ts_epoch.cmp(&b.ts_epoch).then(a.seq.cmp(&b.seq)));
        let mut kept: Vec<AisRow> = Vec::new();
        for point in track {
            if kept.is_empty() {
                kept.push(point);
                continue;
            }
            let prev = kept.last().unwrap();
            let hours = (point.ts_epoch - prev.ts_epoch) as f64 / 3600.0;
            let speed = if hours <= 0.0 {
                0.0
            } else {
                haversine_nm(prev, &point) / hours
            };
            if speed > policy.max_sog_knots {
                removed += 1;
                continue;
            }
            kept.push(point);
        }
        kept_all.extend(kept);
    }
    kept_all.sort_by(|a, b| a.mmsi.cmp(&b.mmsi).then(a.ts_epoch.cmp(&b.ts_epoch)).then(a.seq.cmp(&b.seq)));
    (kept_all, removed)
}
