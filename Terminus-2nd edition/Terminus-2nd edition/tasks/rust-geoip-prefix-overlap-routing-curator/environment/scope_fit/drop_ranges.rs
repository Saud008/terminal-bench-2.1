/// STUB — implement RFC-reserved prefix detection per /app/docs/reserved-range-policy.md
pub fn is_reserved(_cidr: &str) -> bool {
    unimplemented!("STUB: is_reserved — see /app/docs/reserved-range-policy.md")
}

/// STUB — drop reserved prefixes and return (kept, dropped_count).
pub fn filter_records<T, F>(records: Vec<T>, _cidr_of: F) -> (Vec<T>, u32)
where
    F: Fn(&T) -> &str,
{
    let _ = records;
    unimplemented!("STUB: filter_records — see /app/docs/reserved-range-policy.md")
}
