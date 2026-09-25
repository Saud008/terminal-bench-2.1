use serde_json::Value;

pub fn bucket_key(factors: &Value) -> Result<String, String> {
    serde_json::to_string(factors).map_err(|e| e.to_string())
}
