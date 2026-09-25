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
    if player.inventory.iter().any(|i| i == item_id) {
        let delta = season
            .duplicate_shards
            .get(rarity)
            .copied()
            .unwrap_or(0);
        player.shards = player.shards.saturating_add(delta);
        return AuditEntry {
            action: "duplicate_shard".to_string(),
            event_id: event_id.to_string(),
            player_id: String::new(),
            season_id: season.season_id.clone(),
            item_id: item_id.to_string(),
            rarity: rarity.to_string(),
            seq,
            timestamp_ms,
            shard_delta: Some(delta),
            reason: None,
        };
    }
    player.inventory.push(item_id.to_string());
    player.inventory.sort();
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
