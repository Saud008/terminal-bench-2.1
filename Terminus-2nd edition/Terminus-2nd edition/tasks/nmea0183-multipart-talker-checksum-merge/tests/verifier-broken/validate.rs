use crate::model::MergeSnapshot;

/// BROKEN: skips talker-prefix validation.
pub fn validate_snapshot(_snapshot: &MergeSnapshot) -> Result<(), String> {
    Ok(())
}
