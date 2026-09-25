//! Non-authoritative metric wrapper — not on batch-propagate or emit-violations hot path.

pub fn wrap_counter(name: &str, value: u64) -> String {
    format!("counter:{name}={value}")
}
