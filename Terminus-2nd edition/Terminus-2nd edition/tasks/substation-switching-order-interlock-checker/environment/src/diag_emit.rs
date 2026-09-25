use crate::proc_walk;
use crate::yard_model::{VerifyReport, VerifySummary, YardSnapshot, ScenarioFile, LotoTicket};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn build_report(
    snap: &YardSnapshot,
    sf: &ScenarioFile,
    ticket: &LotoTicket,
    seed: &str,
    scenario: &str,
) -> VerifyReport {
    let steps = proc_walk::simulate_procedure(snap, sf);
    let unsafe_count = steps.iter().filter(|s| !s.safe).count() as u32;
    let final_energized = steps.last().map(|s| s.energized_buses.clone()).unwrap_or_default();
    let summary = VerifySummary {
        total_steps: steps.len() as u32,
        unsafe_count,
        final_energized_buses: final_energized,
    };
    let mut rep = VerifyReport {
        seed: seed.to_string(),
        scenario: scenario.to_string(),
        loto_ticket_id: ticket.ticket_id.clone(),
        steps,
        summary,
        audit_digest: String::new(),
    };
    rep.audit_digest = audit_digest(&rep);
    rep
}

pub fn audit_digest(rep: &VerifyReport) -> String {
    let mut idx: Vec<u32> = rep.steps.iter().map(|s| s.step_index).collect();
    idx.sort();
    let body = serde_json::json!({
        "total_steps": rep.summary.total_steps,
        "step_indices": idx,
    });
    let raw = serde_json::to_string(&body).unwrap_or_default();
    hex::encode(Sha256::digest(raw.as_bytes()))
}

pub fn write_report(path: &Path, rep: &VerifyReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(rep).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
