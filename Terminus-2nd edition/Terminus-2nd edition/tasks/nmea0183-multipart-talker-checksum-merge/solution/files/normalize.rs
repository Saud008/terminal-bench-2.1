pub fn canonical_talker(talker: &str) -> String {
    match talker {
        "GP" | "GN" => "GN".to_string(),
        other => other.to_string(),
    }
}
