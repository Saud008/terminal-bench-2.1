use crate::m02_unit_depth;
use crate::m03_crop_kc;
use crate::m04_probe_blend;
use crate::m05_et_deficit;
use crate::field_schema::{FieldLedgerRow, OrchardMeta, MoistureLedger};
use sha2::{Digest, Sha256};

pub fn build_moisture_ledger(run_id: &str, meta: &OrchardMeta) -> MoistureLedger {
    let mut fields = Vec::new();
    for (field_id, spec) in &meta.fields {
        let vwc = m04_probe_blend::blend_probes(&spec.probes);
        let kc = m03_crop_kc::kc_for_stage(&meta.kc_stages, spec.crop_stage);
        let mut et_demands = Vec::new();
        let mut deficits = Vec::new();
        for w in 0..meta.window_count as usize {
            let etf = meta.et_forecast_mm.get(w).copied().unwrap_or(0.0);
            let et_d = m05_et_deficit::et_demand_mm(kc, etf);
            et_demands.push(et_d);
            let gap = m02_unit_depth::vwc_to_mm(vwc, meta.target_vwc, spec.root_depth_cm);
            deficits.push(m05_et_deficit::deficit_mm(gap, et_d));
        }
        fields.push(FieldLedgerRow {
            field_id: field_id.clone(),
            calibrated_vwc: vwc,
            et_demand_mm: et_demands,
            deficit_mm: deficits,
        });
    }
    fields.sort_by(|a, b| a.field_id.cmp(&b.field_id));
    let body = serde_json::json!({
        "field_count": fields.len(),
        "orchard": meta.orchard,
        "run_id": run_id,
        "window_count": meta.window_count,
    });
    let ledger_digest = format!("{:x}", Sha256::digest(body.to_string().as_bytes()));
    MoistureLedger {
        run_id: run_id.to_string(),
        orchard: meta.orchard.clone(),
        window_count: meta.window_count,
        target_vwc: meta.target_vwc,
        fields,
        pump: meta.pump.clone(),
        quota_windows: meta.quota_windows.clone(),
        ledger_digest,
    }
}
