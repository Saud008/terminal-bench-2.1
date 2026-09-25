use crate::m02_unit_depth;
use crate::m06_quota_roll;
use crate::m07_pump_cap;
use crate::field_schema::{DeficitTrace, IrrigationPlan, IrrigationRow, MoistureLedger};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

fn round4(v: f64) -> f64 {
    (v * 10000.0).round() / 10000.0
}

pub fn publish_plan(ledger: &MoistureLedger, meta_fields: &BTreeMap<String, crate::field_schema::FieldSpec>) -> IrrigationPlan {
    let mut assignments = Vec::new();
    let mut trace_rows = Vec::new();
    let mut usage: BTreeMap<u32, f64> = BTreeMap::new();
    let cap = m07_pump_cap::slot_capacity_liters(&ledger.pump);

    for w_idx in 0..ledger.window_count {
        let mut remaining = cap;
        let mut field_order: Vec<_> = ledger.fields.iter().collect();
        field_order.sort_by(|a, b| b.deficit_mm[w_idx as usize].partial_cmp(&a.deficit_mm[w_idx as usize]).unwrap());

        for fs in field_order {
            let before = round4(fs.deficit_mm[w_idx as usize]);
            if before <= 0.0 || remaining <= 0.0 {
                trace_rows.push(DeficitTrace {
                    field_id: fs.field_id.clone(),
                    window_index: w_idx,
                    deficit_before_mm: before,
                    deficit_after_mm: before,
                });
                continue;
            }
            let area = meta_fields.get(&fs.field_id).map(|f| f.area_ha).unwrap_or(1.0);
            let need_liters = m02_unit_depth::liters_from_mm(before, area);
            let applied = round4(need_liters.min(remaining));
            remaining -= applied;
            let applied_mm = if area > 0.0 { applied / (area * 10.0) } else { 0.0 };
            let after = round4((before - applied_mm).max(0.0));
            assignments.push(IrrigationRow {
                field_id: fs.field_id.clone(),
                window_index: w_idx,
                liters_applied: applied,
                deficit_after_mm: after,
            });
            *usage.entry(w_idx).or_insert(0.0) += applied / 1000.0;
            trace_rows.push(DeficitTrace {
                field_id: fs.field_id.clone(),
                window_index: w_idx,
                deficit_before_mm: before,
                deficit_after_mm: after,
            });
        }
    }
    assignments.sort_by(|a, b| (a.field_id.clone(), a.window_index).cmp(&(b.field_id.clone(), b.window_index)));
    trace_rows.sort_by(|a, b| (a.field_id.clone(), a.window_index).cmp(&(b.field_id.clone(), b.window_index)));
    let quota_ledger = m06_quota_roll::build_quota_ledger(&ledger.quota_windows, &usage);
    let mut summary = BTreeMap::new();
    summary.insert("assignment_count".into(), serde_json::json!(assignments.len()));
    let total_liters: f64 = assignments.iter().map(|a| a.liters_applied).sum();
    summary.insert("total_liters".into(), serde_json::json!(round4(total_liters)));
    let digest_body = serde_json::json!({"assignments": assignments, "deficit_trace": trace_rows});
    let plan_digest = format!("{:x}", Sha256::digest(digest_body.to_string().as_bytes()));
    IrrigationPlan {
        run_id: ledger.run_id.clone(),
        assignments,
        quota_ledger,
        deficit_trace: trace_rows,
        summary,
        plan_digest,
    }
}
