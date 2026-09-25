use serde_json::Value;
use sha2::{Digest, Sha256};

/// Closure-stage digest over window integral rows.
/// Keys must serialize as window_id before integral to match reference_xanes.py.
pub fn export_closure_digest(rows: &[Value]) -> String {
    let mut parts = Vec::with_capacity(rows.len());
    for row in rows {
        let window_id = row["window_id"].as_str().expect("window_id");
        let integral = row["integral"].as_f64().expect("integral");
        let integral_json = serde_json::to_string(&integral).expect("integral json");
        parts.push(format!(r#"{{"window_id":"{window_id}","integral":{integral_json}}}"#));
    }
    let compact = format!("[{}]", parts.join(","));
    let mut hasher = Sha256::new();
    hasher.update(compact.as_bytes());
    format!("{:x}", hasher.finalize())
}
