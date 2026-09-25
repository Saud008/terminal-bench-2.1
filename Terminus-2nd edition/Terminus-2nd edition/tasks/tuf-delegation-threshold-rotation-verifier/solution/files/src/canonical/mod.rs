use serde_json::Value;

pub fn canonical_bytes(value: &Value) -> Result<Vec<u8>, String> {
    Ok(canonical_string(value)?.into_bytes())
}

pub fn canonical_string(value: &Value) -> Result<String, String> {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let mut parts = Vec::with_capacity(keys.len());
            for k in keys {
                let key_json = serde_json::to_string(k).map_err(|e| e.to_string())?;
                let val = canonical_string(&map[k])?;
                parts.push(format!("{key_json}:{val}"));
            }
            Ok(format!("{{{}}}", parts.join(",")))
        }
        Value::Array(items) => {
            let mut parts = Vec::with_capacity(items.len());
            for item in items {
                parts.push(canonical_string(item)?);
            }
            Ok(format!("[{}]", parts.join(",")))
        }
        other => serde_json::to_string(other).map_err(|e| e.to_string()),
    }
}
