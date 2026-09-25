use crate::closure_rank;
use crate::correlation_store;
use crate::win_schema::{ClosureReport, ClosureRow, ClosureSummary};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn build_closure(correlation_path: &str, session_id: &str) -> Result<ClosureReport, String> {
    let corr = correlation_store::read_correlation(correlation_path)?;
    if corr.session_id != session_id {
        return Err("correlation session_id mismatch".into());
    }
    let mut rows: Vec<ClosureRow> = corr
        .lots
        .iter()
        .map(|l| ClosureRow {
            lot_id: l.lot_id.clone(),
            severity: l.severity,
            excursion_minutes: l.excursion_minutes,
            extended_expiry: l.extended_expiry.clone(),
            cert_digest: l.cert_digest.clone(),
            quarantine: l.quarantine,
        })
        .collect();
    closure_rank::sort_rows(&mut rows);
    let summary = build_summary(&rows);
    let mut report = ClosureReport {
        session_id: session_id.to_string(),
        bundle: corr.bundle.clone(),
        rows,
        summary: summary.clone(),
        closure_digest: String::new(),
    };
    report.closure_digest = closure_digest(&summary);
    Ok(report)
}

fn build_summary(rows: &[ClosureRow]) -> ClosureSummary {
    let quarantined = rows.iter().filter(|r| r.quarantine).count() as u32;
    let max_severity = rows.iter().map(|r| r.severity).max().unwrap_or(0);
    let excursion_events = rows.iter().filter(|r| r.excursion_minutes > 0).count() as u32;
    ClosureSummary {
        total_lots: rows.len() as u32,
        quarantined,
        max_severity,
        excursion_events,
    }
}

fn closure_digest(summary: &ClosureSummary) -> String {
    let body = format!(
        "{{\"excursion_events\":{},\"max_severity\":{},\"quarantined\":{},\"total_lots\":{}}}",
        summary.excursion_events,
        summary.max_severity,
        summary.quarantined,
        summary.total_lots,
    );
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())
}

pub fn write_closure(path: &Path, report: &ClosureReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(report).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
