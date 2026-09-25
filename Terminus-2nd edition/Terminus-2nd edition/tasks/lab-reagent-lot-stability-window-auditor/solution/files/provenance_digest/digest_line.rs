use sha2::{Digest, Sha256};

pub fn lot_cert_digest(lot_id: &str, as_of_date: &str, assay_code: &str) -> String {
    let body = format!("{lot_id}:{as_of_date}:{assay_code}");
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())[..16].to_string()
}
