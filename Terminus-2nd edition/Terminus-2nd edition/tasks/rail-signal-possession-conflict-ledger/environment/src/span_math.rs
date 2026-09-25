pub fn intervals_overlap(a_start: u64, a_end: u64, b_start: u64, b_end: u64) -> bool {
    a_start <= b_end && b_start <= a_end
}

pub fn clip_window(a_start: u64, a_end: u64, b_start: u64, b_end: u64) -> Option<(u64, u64)> {
    if !intervals_overlap(a_start, a_end, b_start, b_end) {
        return None;
    }
    let start = a_start.max(b_start);
    let end = a_end.min(b_end);
    Some((start, end))
}
