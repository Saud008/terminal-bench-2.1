use crate::forecast::digest;
use crate::forecast::anchor_bind;
use crate::forecast::horizon_ms;
use crate::forecast::slot_pick;
use crate::ledger_store;
use crate::lock_store;
use crate::route_model::ReuseForecastLine;
use std::fs;
use std::path::Path;

pub fn emit_reuse_forecast(_scenario: &str, _root: &str, out_path: &str) -> Result<(), String> {
    if ledger_store::read_run_id() == 0 {
        return Err("run_id must be greater than zero".into());
    }
    let ledger = ledger_store::load_ledger()?;
    let scenario_lock = lock_store::load()?;
    let peer_max = ledger
        .entries
        .values()
        .map(|s| s.last_ts_ms)
        .max()
        .unwrap_or(0);
    let mut lines: Vec<ReuseForecastLine> = Vec::new();
    for (key, slot) in &ledger.entries {
        let (peer_id, prefix) = split_key(key);
        let row = scenario_lock
            .peer_table
            .get(&peer_id)
            .cloned()
            .unwrap_or_else(|| crate::route_model::fallback_peer(&peer_id));
        if !slot_pick::retain_slot(slot, &row) {
            continue;
        }
        let ms = horizon_ms::ms_to_reuse(slot.penalty, row.reuse_threshold, row.half_life_ms)?;
        let epoch = anchor_bind::forecast_anchor_ms(slot, peer_max);
        let dig = digest::slot_digest(
            &peer_id,
            &prefix,
            slot.penalty,
            row.reuse_threshold,
            ms,
            epoch,
        );
        lines.push(ReuseForecastLine {
            peer_id,
            prefix,
            penalty_now: slot.penalty,
            reuse_threshold: row.reuse_threshold,
            half_life_ms: row.half_life_ms,
            ms_to_reuse: ms,
            forecast_anchor_ms: epoch,
            slot_digest: dig,
        });
    }
    lines.sort_by(|a, b| a.prefix.cmp(&b.prefix).then_with(|| a.peer_id.cmp(&b.peer_id)));
    let mut body = String::new();
    for line in lines {
        body.push_str(&serde_json::to_string(&line).map_err(|e| e.to_string())?);
        body.push('\n');
    }
    if let Some(parent) = Path::new(out_path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(out_path, body).map_err(|e| e.to_string())
}

fn split_key(key: &str) -> (String, String) {
    if let Some((p, pref)) = key.split_once(':') {
        (p.to_string(), pref.to_string())
    } else {
        (key.to_string(), String::new())
    }
}
