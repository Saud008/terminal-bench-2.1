use crate::hopf_fold;
use crate::types::{LossEvent, CaptureCache, SampleRow};
use std::fs;
use std::io::Write;
use std::path::Path;

pub fn scan_reflections(plan: &CaptureCache, samples_path: &Path, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(samples_path).map_err(|e| e.to_string())?;
    let mut rows: Vec<SampleRow> = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let v: serde_json::Value = serde_json::from_str(line).map_err(|e| e.to_string())?;
        rows.push(SampleRow {
            distance_m: v["distance_m"].as_f64().unwrap_or(0.0),
            power_dbm: v["power_dbm"].as_f64().unwrap_or(0.0),
            epoch: v["epoch"].as_u64().unwrap_or(0) as u32,
        });
    }
    rows.sort_by(|a, b| a.distance_m.partial_cmp(&b.distance_m).unwrap());
    let threshold = plan.loss_threshold_db;
    let mut events: Vec<LossEvent> = Vec::new();
    for pair in rows.windows(2) {
        let prev = &pair[0];
        let cur = &pair[1];
        let delta = prev.power_dbm - cur.power_dbm;
        if delta >= threshold {
            events.push(LossEvent {
                distance_m: cur.distance_m,
                measured_loss_db: (delta * 1000.0).round() / 1000.0,
                epoch: cur.epoch,
            });
        }
    }
    let tol = crate::reflection_tol_override().unwrap_or(plan.reflection_tolerance_m);
    let (events, suppressed) = hopf_fold::suppress_duplicates(events, tol);
    let out_path = format!("{out_dir}/{}.jsonl", plan.run_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    let hdr = serde_json::json!({
        "run_id": plan.run_id,
        "suppressed_duplicate_count": suppressed,
    });
    writeln!(f, "{}", hdr).map_err(|e| e.to_string())?;
    for ev in events {
        let js = serde_json::to_string(&ev).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
