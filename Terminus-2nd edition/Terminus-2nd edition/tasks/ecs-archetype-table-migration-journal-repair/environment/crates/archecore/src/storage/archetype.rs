use sha2::{Digest, Sha256};

use crate::model::ComponentId;

pub fn archetype_hash(rows: &[(ComponentId, u32)]) -> u64 {
    let mut hasher = Sha256::new();
    for (id, align) in rows {
        hasher.update(id.to_le_bytes());
        hasher.update(align.to_be_bytes());
    }
    let digest = hasher.finalize();
    u64::from_le_bytes(digest[..8].try_into().expect("slice"))
}

pub fn hash_hex(rows: &[(ComponentId, u32)]) -> String {
    format!("{:016x}", archetype_hash(rows))
}
