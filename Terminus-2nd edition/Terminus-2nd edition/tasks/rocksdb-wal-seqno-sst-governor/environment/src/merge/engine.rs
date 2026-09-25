pub fn apply_key_prefix(key: &str) -> String {
    if let Ok(prefix) = std::env::var("TB3_KEY_PREFIX") {
        if !prefix.is_empty() {
            return format!("{prefix}{key}");
        }
    }
    key.to_string()
}
