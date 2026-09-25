use crate::mw01;
use crate::mw11::{ScenarioMeta, HarmonizedLedger};
use sha2::{Digest, Sha256};

pub fn curate_run(run_id: &str, meta: &ScenarioMeta) -> HarmonizedLedger {
    let windows = mw01::normalize_windows(meta.slot_minutes, meta.window_count);
    let body = serde_json::json!({
        "intensity_keys": meta.intensity.keys().collect::<Vec<_>>(),
        "job_count": meta.jobs.len(),
        "run_id": run_id,
        "scenario": meta.scenario,
        "window_count": meta.window_count,
    });
    let harmonized_digest = format!("{:x}", Sha256::digest(body.to_string().as_bytes()));
    HarmonizedLedger {
        run_id: run_id.to_string(),
        scenario: meta.scenario.clone(),
        slot_minutes: meta.slot_minutes,
        window_count: meta.window_count,
        regions: meta.regions.clone(),
        intensity: meta.intensity.clone(),
        jobs: meta.jobs.clone(),
        normalized_windows: windows,
        harmonized_digest,
    }
}
