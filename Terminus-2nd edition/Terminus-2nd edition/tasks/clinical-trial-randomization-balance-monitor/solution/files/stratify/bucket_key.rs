use serde_json::Value;

pub fn bucket_key(factors: &Value) -> Result<String, String> {
    let obj = factors.as_object().ok_or("factors object")?;
    let mut map = serde_json::Map::new();
    let mut keys: Vec<&String> = obj.keys().collect();
    keys.sort();
    for k in keys {
        map.insert(k.clone(), obj[k].clone());
    }
    serde_json::to_string(&serde_json::Value::Object(map)).map_err(|e| e.to_string())
}
