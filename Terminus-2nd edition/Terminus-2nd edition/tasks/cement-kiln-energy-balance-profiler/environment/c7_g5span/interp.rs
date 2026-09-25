use crate::types::ProbeWindow;

pub fn fill_gaps(
    mut points: Vec<(u64, String, f64)>,
    grid_step: u64,
    batch_lookup: &dyn Fn(u64) -> Option<String>,
) -> Vec<ProbeWindow> {
    if points.is_empty() {
        return Vec::new();
    }
    points.sort_by_key(|p| p.0);
    let min_ts = points.first().unwrap().0;
    let max_ts = points.last().unwrap().0;
    let mut out = Vec::new();
    let mut idx = 0;
    let mut ts = min_ts;
    while ts <= max_ts {
        while idx + 1 < points.len() && points[idx + 1].0 <= ts {
            idx += 1;
        }
        let (t0, pid, v0) = &points[idx];
        let interpolated = *t0 != ts;
        let batch_id = batch_lookup(ts).unwrap_or_default();
        out.push(ProbeWindow {
            probe_ts: ts,
            probe_id: pid.clone(),
            temp_c: *v0,
            batch_id,
            interpolated,
        });
        ts += grid_step;
    }
    out
}
