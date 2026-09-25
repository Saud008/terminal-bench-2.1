use crate::model::{GenerationFile, PityLedgerFile, SettlementReport, StagingSnapshot};

pub fn build_report(
    staging: &StagingSnapshot,
    ledger: &PityLedgerFile,
    generation: &GenerationFile,
    audit_log: Vec<crate::model::AuditEntry>,
) -> Result<SettlementReport, String> {
    let _ = (staging, generation);
    let mut sorted_audit = audit_log;
    sorted_audit.sort_by(|a, b| a.event_id.cmp(&b.event_id));
    Ok(SettlementReport {
        audit_log: sorted_audit,
        events_digest: String::new(),
        generation: generation.generation,
        layout_version: 1,
        players: ledger.players.clone(),
        pool_epoch: staging.pool_epoch,
        season_id: staging.season_id.clone(),
        settlement_digest: String::new(),
        staging_generation: staging.staging_generation,
    })
}

pub fn compute_settlement_digest(_report: &SettlementReport) -> Result<String, String> {
    Ok(String::new())
}

pub fn sorted_report_json(report: &SettlementReport) -> Result<String, String> {
    serde_json::to_string_pretty(report).map_err(|e| e.to_string())
}

pub fn audit_processing_order(events: &[crate::model::PullEvent]) -> Vec<(u64, u64, String)> {
    events
        .iter()
        .map(|e| (e.timestamp_ms, e.seq, e.event_id.clone()))
        .collect()
}
