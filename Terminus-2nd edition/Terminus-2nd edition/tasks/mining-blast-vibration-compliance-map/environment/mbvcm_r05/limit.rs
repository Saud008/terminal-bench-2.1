use crate::limit_scale;
use crate::types::LimitTable;

pub fn pick_threshold(structure_class: &str, fired_at: &str, limits: &LimitTable, _tz_hours: i32) -> f64 {
    let pair = match structure_class {
        "industrial" => &limits.industrial,
        _ => &limits.residential,
    };
    pair.day_mm_s * limit_scale()
}
