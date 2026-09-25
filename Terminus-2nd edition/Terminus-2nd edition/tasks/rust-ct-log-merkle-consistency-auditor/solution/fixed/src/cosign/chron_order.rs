fn chron_ok(older_ts: u64, newer_ts: u64) -> bool {
    newer_ts > older_ts
}

fn size_advances(older_size: u64, newer_size: u64) -> bool {
    newer_size > older_size
}

pub fn timestamps_monotonic(older_ts: u64, newer_ts: u64, older_size: u64, newer_size: u64) -> bool {
    if !size_advances(older_size, newer_size) {
        return true;
    }
    chron_ok(older_ts, newer_ts)
}



