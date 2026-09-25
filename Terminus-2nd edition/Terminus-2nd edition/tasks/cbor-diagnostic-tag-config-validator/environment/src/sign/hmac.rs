use std::fs;

use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};

type HmacSha256 = Hmac<Sha256>;

const KEY_PATH: &str = "/app/config/signing.key";

pub fn sha256_hex(data: &[u8]) -> String {
    let digest = Sha256::digest(data);
    hex::encode(digest)
}

pub fn hmac_sha256_hex(data: &[u8]) -> Result<String, String> {
    let key = fs::read(KEY_PATH).map_err(|e| e.to_string())?;
    let mut mac =
        HmacSha256::new_from_slice(&key).map_err(|e| format!("invalid hmac key: {}", e))?;
    mac.update(data);
    Ok(hex::encode(mac.finalize().into_bytes()))
}
