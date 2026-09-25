use sha2::{Digest, Sha256};

pub fn arc_ppm_fingerprint(chem_id: &str, lot_code: &str, as_of: &str) -> String {
    let body = format!("{chem_id}:{lot_code}:{as_of}");
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())[..16].to_string()
}
