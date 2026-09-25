use crate::mw02;
use crate::mw03;
use crate::mw04;
use crate::mw05;
use crate::mw06;
use crate::mw11::{AssignmentRow, InfeasRow, ShiftAtlas, HarmonizedLedger};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

pub fn publish_atlas(ledger: &HarmonizedLedger) -> ShiftAtlas {
    let mut assignments = Vec::new();
    let mut infeas_rows: Vec<InfeasRow> = Vec::new();
    let mut usage: BTreeMap<(String, u32), u32> = BTreeMap::new();
    let mut jobs = ledger.jobs.clone();
    jobs.sort_by(|a, b| (a.deadline_slot, a.job_id.clone()).cmp(&(b.deadline_slot, b.job_id.clone())));

    for job in &jobs {
        let mut best: Option<(String, u32, f64)> = None;
        for (region, curve) in &ledger.intensity {
            if !mw03::region_allowed(region, &job.allowed_regions) {
                continue;
            }
            for start in 0..ledger.window_count {
                if !mw04::deadline_ok(start, job.duration_slots, job.deadline_slot) {
                    continue;
                }
                let mass = mw05::carbon_mass(curve, job, start);
                let replace = match &best {
                    None => true,
                    Some((_, _, bm)) => mass < *bm,
                };
                if replace {
                    best = Some((region.clone(), start, mass));
                }
            }
        }
        if let Some((region, start, mass)) = best {
            for s in start..start + job.duration_slots {
                *usage.entry((region.clone(), s)).or_insert(0) += job.compute_units;
            }
            assignments.push(AssignmentRow {
                job_id: job.job_id.clone(),
                region,
                start_slot: start,
                carbon_mass_g: mass,
            });
        } else {
            mw06::record_infeasible(&job.job_id, "QUOTA", &mut infeas_rows);
        }
    }
    assignments.sort_by(|a, b| (a.job_id.clone(), a.region.clone()).cmp(&(b.job_id.clone(), b.region.clone())));
    let quota_ledger = mw02::build_quota_ledger(&ledger.regions, ledger.window_count, &usage);
    let mut summary = BTreeMap::new();
    summary.insert("feasible_count".into(), serde_json::json!(assignments.len()));
    summary.insert("infeasible_count".into(), serde_json::json!(infeas_rows.len()));
    let total_carbon: f64 = assignments.iter().map(|a| a.carbon_mass_g).sum();
    summary.insert("total_carbon_mass_g".into(), serde_json::json!(total_carbon));
    let digest_body = serde_json::json!({
        "assignments": assignments,
        "blocked_jobs": infeas_rows,
    });
    let plan_digest = format!("{:x}", Sha256::digest(digest_body.to_string().as_bytes()));
    ShiftAtlas {
        run_id: ledger.run_id.clone(),
        assignments,
        quota_ledger,
        blocked_jobs: infeas_rows,
        summary,
        plan_digest,
    }
}
