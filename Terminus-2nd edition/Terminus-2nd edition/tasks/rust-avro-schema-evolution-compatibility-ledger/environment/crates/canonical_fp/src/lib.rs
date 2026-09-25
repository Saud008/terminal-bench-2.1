use avsc_json::AvroSchema;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

pub fn parsing_fingerprint(schema: &AvroSchema) -> String {
    let canon = canonicalize(&schema.raw);
    let bytes = serde_json::to_vec(&canon).unwrap_or_default();
    let digest = Sha256::digest(bytes);
    digest.iter().map(|b| format!("{b:02x}")).collect::<String>()[..16].to_string()
}

fn canonicalize(v: &Value) -> Value {
    match v {
        Value::Object(map) => {
            let mut out = Map::new();
            for (k, val) in map {
                if k == "doc" || k == "default" || k == "aliases" {
                    continue;
                }
                let cleaned = if k == "fields" && map.get("type").and_then(|t| t.as_str()) == Some("record") {
                    canonicalize_fields(val)
                } else {
                    canonicalize(val)
                };
                out.insert(k.clone(), cleaned);
            }
            Value::Object(out)
        }
        Value::Array(arr) => Value::Array(arr.iter().map(canonicalize).collect()),
        other => other.clone(),
    }
}

fn canonicalize_fields(v: &Value) -> Value {
    match v {
        Value::Array(arr) => {
            let fields: Vec<Value> = arr.iter().map(canonicalize).collect();
            Value::Array(fields)
        }
        other => canonicalize(other),
    }
}
