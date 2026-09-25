use crate::error::FitError;

pub fn read_lap_start_time(bytes: &[u8]) -> Result<u32, FitError> {
    if bytes.len() < 4 {
        return Err(FitError::Parse("lap start_time missing".to_string()));
    }
    Ok(u32::from_be_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
}
