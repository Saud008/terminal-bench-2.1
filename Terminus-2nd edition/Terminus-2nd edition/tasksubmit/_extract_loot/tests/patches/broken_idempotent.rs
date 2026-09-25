use crate::model::{AuditEntry, ProcessedEventsFile};

pub fn already_processed(_processed: &ProcessedEventsFile, _event_id: &str) -> bool {
    false
}

pub fn record_processed(processed: &mut ProcessedEventsFile, event_id: &str) {
    processed.event_ids.push(event_id.to_string());
}

pub fn duplicate_skip_audit(
    event_id: &str,
    player_id: &str,
    season_id: &str,
    item_id: &str,
    rarity: &str,
    seq: u64,
    timestamp_ms: u64,
) -> AuditEntry {
    AuditEntry {
        action: "duplicate_skip".to_string(),
        event_id: event_id.to_string(),
        player_id: player_id.to_string(),
        season_id: season_id.to_string(),
        item_id: item_id.to_string(),
        rarity: rarity.to_string(),
        seq,
        timestamp_ms,
        shard_delta: None,
        reason: Some("duplicate_event_id".to_string()),
    }
}
