use serde_json::Value;
use std::fs;
use std::path::Path;

pub fn load_json(path: &Path) -> Result<Value, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn is_object(v: &Value) -> bool {
    v.is_object()
}

pub fn object_get<'a>(v: &'a Value, key: &str) -> Option<&'a Value> {
    v.as_object()?.get(key)
}
