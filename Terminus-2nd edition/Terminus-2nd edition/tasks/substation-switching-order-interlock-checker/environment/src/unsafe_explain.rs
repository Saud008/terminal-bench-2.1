pub fn normalize_codes(mut codes: Vec<String>) -> Vec<String> {
    codes.sort();
    codes.dedup();
    codes
}

pub fn explain(code: &str) -> &'static str {
    match code {
        "lockout_active" => "equipment under active lockout",
        "close_blocked_energized" => "close blocked by energization",
        "open_parallel_risk" => "open would breach parallel isolation",
        "out_of_order" => "procedure step index out of order",
        "unknown_breaker" => "breaker not in yard snapshot",
        _ => "unsafe operation",
    }
}
