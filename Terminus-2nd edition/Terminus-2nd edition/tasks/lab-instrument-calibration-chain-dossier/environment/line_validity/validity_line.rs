use sha2::{Digest, Sha256};

pub fn cert_digest(instrument_id: &str, as_of_date: &str, cert_id: &str) -> String {
    let body = format!("{cert_id}:{instrument_id}:{as_of_date}");
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())[..16].to_string()
}

pub fn cert_valid_on_date(expires: &str, as_of: &str) -> bool {
    expires >= as_of
}
