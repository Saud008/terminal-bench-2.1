use crate::model::{PlayerLedger, SeasonConfig};

pub fn apply_season_carryover(
    player: &mut PlayerLedger,
    _old_season: &SeasonConfig,
    new_season: &SeasonConfig,
) {
    let carried = (player.pity_legendary as f64 * new_season.carry_ratio).floor() as u64;
    player.pity_legendary = carried;
    player.season_id = new_season.season_id.clone();
}

pub fn apply_pity_after_pull(player: &mut PlayerLedger, rarity: &str) {
    if rarity == "legendary" {
        player.pity_legendary = 0;
    } else {
        player.pity_legendary = player.pity_legendary.saturating_add(1);
    }
}
