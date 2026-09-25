# Oracle solve — task identity carbon-intensity-workload-shift-planner token f332aafb
#!/usr/bin/env bash
set -euo pipefail
cd /app/environment

cat > src/mw01.rs <<'EOF'
use crate::mw11::WindowSlot;

pub fn normalize_windows(slot_minutes: u32, window_count: u32) -> Vec<WindowSlot> {
    let mut out = Vec::new();
    for idx in 0..window_count {
        let start = idx * slot_minutes;
        let end = start + slot_minutes;
        out.push(WindowSlot {
            index: idx,
            start_minute: start,
            end_minute: end,
        });
    }
    out
}

pub fn slot_span_slots(start: u32, duration: u32, _windows: &[WindowSlot]) -> Vec<u32> {
    (start..start + duration).collect()
}
EOF

cat > src/mw02.rs <<'EOF'
use crate::mw11::{QuotaLedgerRow, RegionSpec};
use std::collections::BTreeMap;

pub fn build_quota_ledger(
    regions: &BTreeMap<String, RegionSpec>,
    window_count: u32,
    usage: &BTreeMap<(String, u32), u32>,
) -> Vec<QuotaLedgerRow> {
    let mut rows = Vec::new();
    for (region, spec) in regions {
        let mut carry_in = 0u32;
        for w in 0..window_count {
            let used = usage.get(&(region.clone(), w)).copied().unwrap_or(0);
            let available = spec.quota_per_window + carry_in;
            let leftover = available.saturating_sub(used);
            let carry_out = leftover.min(spec.max_carryover);
            rows.push(QuotaLedgerRow {
                region: region.clone(),
                window_index: w,
                base_quota: spec.quota_per_window,
                carry_in,
                used,
                carry_out,
            });
            carry_in = carry_out;
        }
    }
    rows.sort_by(|a, b| (a.region.clone(), a.window_index).cmp(&(b.region.clone(), b.window_index)));
    rows
}

pub fn available_quota(row: &QuotaLedgerRow) -> u32 {
    row.base_quota + row.carry_in
}
EOF

cat > src/mw03.rs <<'EOF'
pub fn region_allowed(region: &str, allowed: &[String]) -> bool {
    allowed.iter().any(|r| r == region)
}
EOF

cat > src/mw04.rs <<'EOF'
pub fn deadline_ok(start_slot: u32, duration_slots: u32, deadline_slot: u32) -> bool {
    start_slot + duration_slots - 1 <= deadline_slot
}
EOF

cat > src/mw05.rs <<'EOF'
use crate::mw11::JobSpec;

pub fn carbon_mass(intensity: &[f64], job: &JobSpec, start_slot: u32) -> f64 {
    slot_intensity_sum(intensity, start_slot, job.duration_slots, job.compute_units)
}

pub fn slot_intensity_sum(intensity: &[f64], start: u32, duration: u32, compute: u32) -> f64 {
    let mut sum = 0.0;
    for s in start..start + duration {
        sum += intensity.get(s as usize).copied().unwrap_or(999.0);
    }
    sum * compute as f64
}
EOF

cat > src/mw06.rs <<'EOF'
use crate::mw11::InfeasRow;

pub fn record_infeasible(job_id: &str, reason: &str, out: &mut Vec<InfeasRow>) {
    out.push(InfeasRow {
        job_id: job_id.to_string(),
        reason: reason.to_string(),
    });
}
EOF

cat > src/mw08.rs <<'EOF'
use crate::mw02;
use crate::mw03;
use crate::mw04;
use crate::mw05;
use crate::mw06;
use crate::mw11::{AssignmentRow, InfeasRow, ShiftAtlas, HarmonizedLedger};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

fn can_place(
    usage: &BTreeMap<(String, u32), u32>,
    ledger: &HarmonizedLedger,
    region: &str,
    start: u32,
    duration: u32,
    compute: u32,
) -> bool {
    let mut temp = usage.clone();
    for s in start..start + duration {
        *temp.entry((region.to_string(), s)).or_insert(0) += compute;
    }
    let ledger = mw02::build_quota_ledger(&ledger.regions, ledger.window_count, &temp);
    for s in start..start + duration {
        let row = ledger
            .iter()
            .find(|r| r.region == region && r.window_index == s)
            .expect("ledger row");
        if row.used > row.base_quota + row.carry_in {
            return false;
        }
    }
    true
}

pub fn publish_atlas(ledger: &HarmonizedLedger) -> ShiftAtlas {
    let mut assignments = Vec::new();
    let mut infeas_rows: Vec<InfeasRow> = Vec::new();
    let mut usage: BTreeMap<(String, u32), u32> = BTreeMap::new();
    let mut jobs = ledger.jobs.clone();
    jobs.sort_by(|a, b| (a.deadline_slot, a.job_id.clone()).cmp(&(b.deadline_slot, b.job_id.clone())));

    for job in &jobs {
        let mut best: Option<(String, u32, f64)> = None;
        let mut residency_fail = true;
        let mut deadline_fail = true;
        for (region, curve) in &ledger.intensity {
            if !mw03::region_allowed(region, &job.allowed_regions) {
                continue;
            }
            residency_fail = false;
            for start in 0..ledger.window_count {
                if !mw04::deadline_ok(start, job.duration_slots, job.deadline_slot) {
                    continue;
                }
                deadline_fail = false;
                if !can_place(&usage, ledger, region, start, job.duration_slots, job.compute_units) {
                    continue;
                }
                let mass = mw05::carbon_mass(curve, job, start);
                let replace = match &best {
                    None => true,
                    Some((br, bs, bm)) => {
                        mass < *bm || (mass == *bm && (region.as_str(), start) < (br.as_str(), *bs))
                    }
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
        } else if residency_fail {
            mw06::record_infeasible(&job.job_id, "RESIDENCY", &mut infeas_rows);
        } else if deadline_fail {
            mw06::record_infeasible(&job.job_id, "DEADLINE", &mut infeas_rows);
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
EOF

CARGO_TARGET_DIR=/app/environment/target /usr/local/cargo/bin/cargo build --release --locked
install -m 0755 target/release/shift-pl /app/bin/shift-pl
