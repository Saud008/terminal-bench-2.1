use crate::tasking_types::{PreemptionEvent, SlotAssignment, TaskPlanManifest};
use sha2::{Digest, Sha256};

fn round4(v: f64) -> f64 {
    (v * 10000.0).round() / 10000.0
}

pub fn plan_digest(manifest: &TaskPlanManifest) -> String {
    let payload = serde_json::json!({
        "scenario_id": manifest.scenario_id,
        "assignment_count": manifest.assignment_count,
        "assignments": manifest.assignments,
        "preemption_trace": manifest.preemption_trace,
        "mean_cloud_risk": manifest.mean_cloud_risk,
    });
    let body = payload.to_string();
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    format!("sha256:{:x}", hasher.finalize())
}

pub fn build_manifest(
    token: &str,
    scenario_id: &str,
    constellation_id: &str,
    assignments: Vec<SlotAssignment>,
    preemptions: Vec<PreemptionEvent>,
) -> TaskPlanManifest {
    let mean = if assignments.is_empty() {
        0.0
    } else {
        round4(assignments.iter().map(|a| a.cloud_composite).sum::<f64>() / assignments.len() as f64)
    };
    let mut manifest = TaskPlanManifest {
        run_token: token.to_string(),
        scenario_id: scenario_id.to_string(),
        constellation_id: constellation_id.to_string(),
        assignment_count: assignments.len() as u32,
        preemption_count: preemptions.len() as u32,
        assignments,
        preemption_trace: preemptions,
        mean_cloud_risk: mean,
        plan_digest: String::new(),
    };
    manifest.plan_digest = plan_digest(&manifest);
    manifest
}
