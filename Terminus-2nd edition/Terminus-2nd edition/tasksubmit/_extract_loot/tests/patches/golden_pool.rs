use crate::model::SeasonConfig;

pub mod weight_merge;

pub fn validate_pool_epoch(event_epoch: u64, season: &SeasonConfig) -> Result<(), String> {
    if event_epoch != season.pool_epoch {
        return Err(format!(
            "pool epoch mismatch: event {event_epoch} season {}",
            season.pool_epoch
        ));
    }
    Ok(())
}
