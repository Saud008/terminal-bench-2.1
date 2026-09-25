use crate::types::ReadingRow;

pub fn bridge_readings(rows: &[ReadingRow]) -> Vec<ReadingRow> {
    let mut sorted = rows.to_vec();
    sorted.sort_by_key(|r| r.hour_index);
    let mut out = Vec::new();
    for (idx, row) in sorted.iter().enumerate() {
        let mut r = row.clone();
        if row.sensor_flags.contains("salinity_dropout") {
            let prev = sorted.get(idx.saturating_sub(1));
            let next = sorted.get(idx + 1);
            if let (Some(a), Some(b)) = (prev, next) {
                let span = (b.hour_index - a.hour_index) as f64;
                let frac = (row.hour_index - a.hour_index) as f64 / span;
                r.salinity_ppt = a.salinity_ppt + frac * (b.salinity_ppt - a.salinity_ppt);
            }
        }
        if row.sensor_flags.contains("pressure_dropout") {
            if let (Some(a), Some(b)) = (sorted.get(idx.saturating_sub(1)), sorted.get(idx + 1)) {
                let span = (b.hour_index - a.hour_index) as f64;
                let frac = (row.hour_index - a.hour_index) as f64 / span;
                r.pressure_bar = a.pressure_bar + frac * (b.pressure_bar - a.pressure_bar);
            }
        }
        if row.sensor_flags.contains("flow_dropout") {
            if let (Some(a), Some(b)) = (sorted.get(idx.saturating_sub(1)), sorted.get(idx + 1)) {
                let span = (b.hour_index - a.hour_index) as f64;
                let frac = (row.hour_index - a.hour_index) as f64 / span;
                r.flow_m3h = a.flow_m3h + frac * (b.flow_m3h - a.flow_m3h);
            }
        }
        out.push(r);
    }
    out
}
