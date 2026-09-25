pub fn windows_overlap(a_start: u64, a_end: u64, b_start: u64, b_end: u64) -> bool {
    a_start < b_end && b_start < a_end
}

pub fn padded_end(imaging_end: u64, setup_pad: u64) -> u64 {
    imaging_end.saturating_add(setup_pad)
}

pub fn windows_overlap_with_setup(
    a_start: u64,
    a_end: u64,
    a_setup: u64,
    b_start: u64,
    b_end: u64,
    b_setup: u64,
) -> bool {
    let a_pad = padded_end(a_end, a_setup);
    let b_pad = padded_end(b_end, b_setup);
    a_start < b_pad && b_start < a_pad
}
