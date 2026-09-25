use crate::types::ProbeWindow;

pub fn fill_gaps(
    points: Vec<(u64, String, f64)>,
    grid_step: u64,
    batch_lookup: &dyn Fn(u64) -> Option<String>,
) -> Vec<ProbeWindow> {
    if points.is_empty() {
        return Vec::new();
    }
    let mut uniq = points;
    uniq.sort_by_key(|p| p.0);
    let min_ts = uniq.first().unwrap().0;
    let max_ts = uniq.last().unwrap().0;
    let mut out = Vec::new();
    let mut ts = min_ts;
    while ts <= max_ts {
        let exact = uniq.iter().find(|p| p.0 == ts);
        let (temp_c, pid, interpolated) = if let Some((_, id, v)) = exact {
            (*v, id.clone(), false)
        } else {
            let lower = uniq.iter().rev().find(|p| p.0 < ts);
            let upper = uniq.iter().find(|p| p.0 > ts);
            match (lower, upper) {
                (Some(l), Some(u)) => {
                    let frac = (ts - l.0) as f64 / (u.0 - l.0) as f64;
                    let v = l.2 + frac * (u.2 - l.2);
                    (v, l.1.clone(), true)
                }
                _ => {
                    ts += grid_step;
                    continue;
                }
            }
        };
        let batch_id = batch_lookup(ts).unwrap_or_default();
        out.push(ProbeWindow {
            probe_ts: ts,
            probe_id: pid,
            temp_c,
            batch_id,
            interpolated,
        });
        ts += grid_step;
    }
    out
}
