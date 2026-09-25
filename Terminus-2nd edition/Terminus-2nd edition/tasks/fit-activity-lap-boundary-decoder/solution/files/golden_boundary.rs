use crate::error::FitError;
use crate::message::LapMsg;

pub fn validate_boundaries(lap: &LapMsg, enforce_decode_alignment: bool) -> Result<(), FitError> {
    if lap.end_time <= lap.start_time {
        return Err(FitError::Parse("end_time must be greater than start_time".to_string()));
    }
    if enforce_decode_alignment && (lap.start_time % 60 != 0 || lap.distance_m % 10 != 0) {
        return Err(FitError::Parse(
            "decode rejected lap due to alignment contract".to_string(),
        ));
    }
    Ok(())
}
