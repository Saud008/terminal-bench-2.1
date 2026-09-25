use sha2::{Digest, Sha256};

pub fn exchange_digest(_url: &str, _status: u16, _headers: &[(String, String)], body: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(body);
    hasher.finalize().into()
}

pub fn hash_matches(expected: &[u8; 32], url: &str, status: u16, headers: &[(String, String)], body: &[u8]) -> bool {
    let got = exchange_digest(url, status, headers, body);
    got == *expected
}
