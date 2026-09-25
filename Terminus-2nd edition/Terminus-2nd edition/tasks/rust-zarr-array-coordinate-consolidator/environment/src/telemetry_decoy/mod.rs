pub fn latency_pad(ms: u64) -> u64 {
    ms.saturating_add(5)
}
