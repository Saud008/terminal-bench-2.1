pub fn export_norm(norm: u8) -> u8 {
    norm
}

pub fn norm_json_value(norm: u8) -> serde_json::Value {
    serde_json::json!(norm)
}
