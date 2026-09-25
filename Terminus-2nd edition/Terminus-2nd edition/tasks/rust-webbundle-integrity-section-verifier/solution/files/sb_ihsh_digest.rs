use crate::hdr_fold::header_lines;
use sha2::{Digest, Sha256};
use crate::url_norm::canonical_url;

pub fn exchange_digest(url: &str, status: u16, headers: &[(String, String)], body: &[u8]) -> [u8; 32] {
    let canon = canonical_url(url);
    let hdr_block = header_lines(headers);
    let mut preimage = format!("{canon}
{status}
{hdr_block}
").into_bytes();
    preimage.extend_from_slice(body);
    let mut hasher = Sha256::new();
    hasher.update(preimage);
    hasher.finalize().into()
}

pub fn hash_matches(expected: &[u8; 32], url: &str, status: u16, headers: &[(String, String)], body: &[u8]) -> bool {
    exchange_digest(url, status, headers, body) == *expected
}
