use crate::ledger_store;
use crate::lock_store;
use crate::route_model::SuppressionLine;
use std::fs;
use std::path::Path;

pub fn emit_atlas(_scenario: &str, _root: &str, out_path: &str) -> Result<(), String> {
    if ledger_store::read_run_id() == 0 {
        return Err("run_id must be greater than zero".into());
    }
    let ledger = ledger_store::load_ledger()?;
    let scenario_lock = lock_store::load()?;
    let mut lines: Vec<SuppressionLine> = Vec::new();
    for (key, slot) in &ledger.entries {
        let (peer_id, prefix) = split_key(key);
        let row = scenario_lock
            .peer_table
            .get(&peer_id)
            .cloned()
            .unwrap_or_else(|| crate::route_model::fallback_peer(&peer_id));
        if slot.flap_count == 0 && !slot.suppressed && slot.peak_penalty < row.reuse_threshold {
            continue;
        }
        lines.push(SuppressionLine {
            peer_id,
            prefix,
            final_penalty: slot.penalty,
            suppressed: slot.suppressed,
            flap_count: slot.flap_count,
            peak_penalty: slot.peak_penalty,
            stable_at_ms: slot.stable_at_ms,
        });
    }
    lines.sort_by(|a, b| a.peer_id.cmp(&b.peer_id).then_with(|| a.prefix.cmp(&b.prefix)));
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
