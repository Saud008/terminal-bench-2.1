use hmac::{Hmac, Mac};
use serde_json::Value;
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

pub fn canonical_body_json(value: &Value) -> Result<String, String> {
    let obj = value.as_object().ok_or_else(|| "event must be object".to_string())?;
    let mut keys: Vec<&String> = obj.keys().filter(|k| *k != "signature").collect();
    keys.sort();
    let mut out = serde_json::Map::new();
    for key in keys {
        out.insert(key.clone(), obj[key].clone());
    }
    serde_json::to_string(&out).map_err(|e| e.to_string())
}

pub fn verify_event_signature(event: &Value, secret: &str) -> Result<(), String> {
    let provided = event
        .get("signature")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "missing signature".to_string())?;
    let canonical = canonical_body_json(event)?;
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).map_err(|e| e.to_string())?;
    mac.update(canonical.as_bytes());
    let expected = hex::encode(mac.finalize().into_bytes());
    if expected != provided {
        return Err("signature mismatch".to_string());
    }
    Ok(())
}
