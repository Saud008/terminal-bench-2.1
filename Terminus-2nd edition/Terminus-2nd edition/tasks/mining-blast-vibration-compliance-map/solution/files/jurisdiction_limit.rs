use crate::limit_scale;
use crate::types::LimitTable;

fn local_hour(fired_at: &str, tz_hours: i32) -> i32 {
    let hour: i32 = fired_at[11..13].parse().unwrap_or(0);
    (hour + tz_hours).rem_euclid(24)
}

pub fn pick_threshold(structure_class: &str, fired_at: &str, limits: &LimitTable, tz_hours: i32) -> f64 {
    let pair = match structure_class {
        "industrial" => &limits.industrial,
        _ => &limits.residential,
    };
    let h = local_hour(fired_at, tz_hours);
    let base = if (7..=18).contains(&h) { pair.day_mm_s } else { pair.night_mm_s };
    base * limit_scale()
}
