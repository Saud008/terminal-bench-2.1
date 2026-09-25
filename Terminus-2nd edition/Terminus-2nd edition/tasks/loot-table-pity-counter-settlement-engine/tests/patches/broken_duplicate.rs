use crate::model::{AuditEntry, PlayerLedger, SeasonConfig};

pub fn process_grant(
    player: &mut PlayerLedger,
    season: &SeasonConfig,
    event_id: &str,
    item_id: &str,
    rarity: &str,
    seq: u64,
    timestamp_ms: u64,
) -> AuditEntry {
    player.inventory.push(item_id.to_string());
    player.inventory.sort();
    let _ = season.duplicate_shards.get(rarity);
    AuditEntry {
        action: "grant".to_string(),
        event_id: event_id.to_string(),
        player_id: String::new(),
        season_id: season.season_id.clone(),
        item_id: item_id.to_string(),
        rarity: rarity.to_string(),
        seq,
        timestamp_ms,
        shard_delta: None,
        reason: None,
    }
}
