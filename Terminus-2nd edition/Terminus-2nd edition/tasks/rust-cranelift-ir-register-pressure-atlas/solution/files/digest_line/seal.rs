use crate::fluence_models::ClosureAtlas;
use sha2::{Digest, Sha256};

/// Canonical closure digest over every atlas field except closure_digest, keys sorted at every
/// nesting level (serde_json's default `Map` is a `BTreeMap`, so converting through `Value`
/// naturally sorts keys the same way Python's `json.dumps(obj, sort_keys=True)` does).
pub fn closure_digest(atlas: &ClosureAtlas) -> String {
    let mut value = serde_json::to_value(atlas).expect("atlas to value");
    if let serde_json::Value::Object(ref mut map) = value {
        map.remove("closure_digest");
    }
    let body = serde_json::to_string(&value).expect("canonical body");
    let hash = Sha256::digest(body.as_bytes());
    hex::encode(hash)
}

/// Render the sealed atlas body for the output file, pretty-printed with one trailing newline.
pub fn render_atlas_body(atlas: &ClosureAtlas) -> String {
    let pretty = serde_json::to_string_pretty(atlas).expect("pretty atlas");
    format!("{pretty}\n")
}
