use crate::header_canon::protected_label_order;
use crate::model::{parse_sign1, value_as_i64, value_as_text, CoseSign1, LABEL_ALG, LABEL_KID};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn write_staging(staging_path: &str, input_path: &str, sign1: &CoseSign1) -> Result<(), String> {
    let order = protected_label_order(&sign1.protected);
    let outer_alg = sign1
        .protected
        .get(&LABEL_ALG)
        .and_then(value_as_i64)
        .unwrap_or(0);
    let outer_kid = sign1
        .protected
        .get(&LABEL_KID)
        .and_then(value_as_text);
    let digest = Sha256::digest(fs::read(input_path).map_err(|e| e.to_string())?);
    let body = json!({
        "input_path": input_path,
        "input_sha256": hex::encode(digest),
        "payload_len": sign1.payload.len(),
        "outer_alg": outer_alg,
        "outer_kid": outer_kid,
        "countersign_count": sign1.countersigns.len(),
        "protected_key_order": order,
    });
    if let Some(parent) = Path::new(staging_path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(&body).map_err(|e| e.to_string())?;
    fs::write(staging_path, format!("{text}\n")).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn sha256_file(path: &str) -> Result<String, String> {
    let bytes = fs::read(path).map_err(|e| e.to_string())?;
    Ok(hex::encode(Sha256::digest(bytes)))
}

pub fn parse_for_staging(bytes: &[u8]) -> Result<CoseSign1, String> {
    parse_sign1(bytes)
}
