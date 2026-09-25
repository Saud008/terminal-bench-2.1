use crate::mw11::WindowSlot;

pub fn normalize_windows(slot_minutes: u32, window_count: u32) -> Vec<WindowSlot> {
    let mut out = Vec::new();
    for idx in 0..window_count {
        let start = idx * slot_minutes;
        let end = start + slot_minutes;
        out.push(WindowSlot {
            index: idx,
            start_minute: start,
            end_minute: end,
        });
    }
    out
}
