use serde_json::Value;

/// Canonical JSON bytes for signed metadata verification.
pub fn canonical_bytes(value: &Value) -> Result<Vec<u8>, String> {
    let text = serde_json::to_string(value).map_err(|e| e.to_string())?;
    Ok(text.into_bytes())
}
