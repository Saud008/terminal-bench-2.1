use sha2::{Digest, Sha256};

/// Filter chain hash for a dataset filter list.
pub fn filter_chain_hash(filters: &[String]) -> String {
    let mut sorted = filters.to_vec();
    sorted.sort();
    let joined = sorted.join("|");
    let digest = Sha256::digest(joined.as_bytes());
    hex::encode(digest)
}

pub fn filter_chain_id(filters: &[String]) -> u32 {
    let h = filter_chain_hash(filters);
    let bytes = h.as_bytes();
    u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]])
}
