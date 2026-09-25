use crate::bline_qn;
use crate::types::{BeatGridAudit, Config, NoteStageRow};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn audit_digest(audit: &BeatGridAudit) -> String {
    let mut ids: Vec<String> = audit.notes.iter().map(|n| n.id.clone()).collect();
    ids.sort();
    let body = serde_json::json!({
        "accepted_note_count": audit.accepted_note_count,
        "chart_id": audit.chart_id,
        "rejected_overlap_count": audit.rejected_overlap_count,
        "run_id": audit.run_id,
        "source_ids": ids,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}

pub fn build_audit(cfg: &Config, run_id: &str, ledger: &crate::types::ChartManifest) -> Result<BeatGridAudit, String> {
    let note_path = format!("{}/{}.jsonl", cfg.note_stage_dir, run_id);
    let raw = fs::read_to_string(&note_path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let _hdr = lines.next();
    let mut rows = Vec::new();
    for line in lines {
        rows.push(serde_json::from_str::<NoteStageRow>(line).map_err(|e| e.to_string())?);
    }
    rows.sort_by(|a, b| a.id.cmp(&b.id));
    let rejected = rows.iter().filter(|r| r.rejected_overlap).count() as u32;
            let accepted = rows.len() as u32 - rejected;
            let mut consistent = 0u32;
    for row in &rows {
        let grid = bline_qn::grid_spacing(ledger.ppq, &ledger.time_sigs, ledger.quant_divisor, row.raw_tick);
        if bline_qn::consistency_delta(row.raw_tick, row.quantized_tick, grid) {
            consistent += 1;
        }
    }
    let score = if rows.is_empty() {
        1.0
    } else {
        consistent as f64 / rows.len() as f64
    };
    let audit = BeatGridAudit {
        run_id: run_id.to_string(),
        chart_id: ledger.chart_id.clone(),
        ppq: ledger.ppq,
        tempo_event_count: ledger.tempo_events.len() as u32,
        accepted_note_count: accepted,
        rejected_overlap_count: rejected,
        grid_consistency_score: score,
        notes: rows,
        audit_digest: String::new(),
    };
    let digest = audit_digest(&audit);
    Ok(BeatGridAudit {
        audit_digest: digest,
        ..audit
    })
}

pub fn write_audit(cfg: &Config, run_id: &str, ledger: &crate::types::ChartManifest, output: &Path) -> Result<(), String> {
    let audit = build_audit(cfg, run_id, ledger)?;
    fs::write(output, serde_json::to_string_pretty(&audit).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())
}
