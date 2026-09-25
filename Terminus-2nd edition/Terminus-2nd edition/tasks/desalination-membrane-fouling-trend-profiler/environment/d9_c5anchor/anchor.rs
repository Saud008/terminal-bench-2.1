use crate::types::CleaningEvent;

pub fn apply_cal_offset(salinity_ppt: f64, cal_offset_ppt: f64) -> f64 {
    salinity_ppt + cal_offset_ppt
}

pub fn is_reset_hour(hour: u32, events: &[CleaningEvent]) -> bool {
    events.iter().any(|e| hour > e.hour_index)
}
