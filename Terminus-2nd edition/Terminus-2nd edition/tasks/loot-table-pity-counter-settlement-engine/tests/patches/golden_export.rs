use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

use crate::model::{GenerationFile, PityLedgerFile, SettlementReport, StagingSnapshot};
use crate::staging::{sort_events, verify_staging_digest};

fn sort_json_value(value: serde_json::Value) -> serde_json::Value {
    match value {
        serde_json::Value::Object(map) => {
            let sorted: BTreeMap<String, serde_json::Value> = map
                .into_iter()
                .map(|(k, v)| (k, sort_json_value(v)))
                .collect();
            serde_json::Value::Object(sorted.into_iter().collect())
        }
        serde_json::Value::Array(items) => {
            serde_json::Value::Array(items.into_iter().map(sort_json_value).collect())
        }
        other => other,
    }
}

pub fn build_report(
    staging: &StagingSnapshot,
    ledger: &PityLedgerFile,
    generation: &GenerationFile,
    audit_log: Vec<crate::model::AuditEntry>,
) -> Result<SettlementReport, String> {
    verify_staging_digest(staging)?;
    if generation.generation == 0 {
        return Err("generation gate: settle required".to_string());
    }
    let mut sorted_audit = audit_log;
    sorted_audit.sort_by(|a, b| {
        (a.timestamp_ms, a.seq, a.event_id.as_str())
            .cmp(&(b.timestamp_ms, b.seq, b.event_id.as_str()))
    });
    let mut report = SettlementReport {
        audit_log: sorted_audit,
        events_digest: staging.events_digest.clone(),
        generation: generation.generation,
        layout_version: 1,
        players: ledger.players.clone(),
        pool_epoch: staging.pool_epoch,
        season_id: staging.season_id.clone(),
        settlement_digest: String::new(),
        staging_generation: staging.staging_generation,
    };
    report.settlement_digest = compute_settlement_digest(&report)?;
    Ok(report)
}

pub fn compute_settlement_digest(report: &SettlementReport) -> Result<String, String> {
    let mut value = sort_json_value(serde_json::to_value(report).map_err(|e| e.to_string())?);
    if let serde_json::Value::Object(ref mut map) = value {
        map.remove("settlement_digest");
    }
    let raw = serde_json::to_string(&value).map_err(|e| e.to_string())?;
    let mut hasher = Sha256::new();
    hasher.update(raw.as_bytes());
    Ok(format!("{:x}", hasher.finalize()))
}

pub fn sorted_report_json(report: &SettlementReport) -> Result<String, String> {
    let value = sort_json_value(serde_json::to_value(report).map_err(|e| e.to_string())?);
    serde_json::to_string_pretty(&value).map_err(|e| e.to_string())
}

pub fn audit_processing_order(events: &[crate::model::PullEvent]) -> Vec<(u64, u64, String)> {
    sort_events(events)
        .into_iter()
        .map(|e| (e.timestamp_ms, e.seq, e.event_id))
        .collect()
}
