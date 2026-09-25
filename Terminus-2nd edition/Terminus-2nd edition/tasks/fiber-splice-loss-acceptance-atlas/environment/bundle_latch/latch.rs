use crate::types::{CaptureCache, SplicePlan};
use std::fs;
use std::path::Path;

pub fn load_capture(run_id: &str, manifest_path: &Path, plan_path: &Path, out_dir: &str) -> Result<(), String> {
    let manifest_raw = fs::read_to_string(manifest_path).map_err(|e| e.to_string())?;
    let plan_raw = fs::read_to_string(plan_path).map_err(|e| e.to_string())?;
    let manifest: serde_json::Value = serde_json::from_str(&manifest_raw).map_err(|e| e.to_string())?;
    let plan_v: serde_json::Value = serde_json::from_str(&plan_raw).map_err(|e| e.to_string())?;
    let mut splices = Vec::new();
    if let Some(arr) = plan_v["splices"].as_array() {
        for s in arr {
            splices.push(SplicePlan {
                distance_m: s["distance_m"].as_f64().unwrap_or(0.0),
                splice_type: s["splice_type"].as_str().unwrap_or("").to_string(),
                planned_loss_db: s["planned_loss_db"].as_f64().unwrap_or(0.0),
            });
        }
    }
    let cache_doc = CaptureCache {
        run_id: run_id.to_string(),
        trace_id: manifest["run_id"].as_str().unwrap_or("").to_string(),
        loss_threshold_db: 0.5,
        reflection_tolerance_m: manifest["reflection_tolerance_m"].as_f64().unwrap_or(10.0),
        splices: Vec::new(),
        load_generation: 1,
    };
    let out = format!("{out_dir}/{run_id}.json");
    fs::write(&out, serde_json::to_string_pretty(&cache_doc).unwrap()).map_err(|e| e.to_string())
}
