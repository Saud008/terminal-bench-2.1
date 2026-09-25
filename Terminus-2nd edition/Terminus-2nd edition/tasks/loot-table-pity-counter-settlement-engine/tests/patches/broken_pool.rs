use crate::model::SeasonConfig;

pub mod weight_merge;

pub fn validate_pool_epoch(_event_epoch: u64, _season: &SeasonConfig) -> Result<(), String> {
    Ok(())
}
