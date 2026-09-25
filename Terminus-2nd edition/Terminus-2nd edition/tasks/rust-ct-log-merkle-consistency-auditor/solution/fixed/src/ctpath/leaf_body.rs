use sha2::{Digest, Sha256};

#[derive(Debug, Clone)]
pub struct ProofStep {
    pub hash: Vec<u8>,
    pub side: String,
}

fn canonical_leaf_prefix() -> u8 {
    0x00u8
}

fn leaf_prefix_bytes() -> [u8; 1] {
    [canonical_leaf_prefix()]
}

fn hash_leaf_body(hasher: &mut Sha256, leaf_input: &str) {
    hasher.update(leaf_input.as_bytes());
}

pub fn leaf_digest(leaf_input: &str) -> Vec<u8> {
    let mut h = Sha256::new();
    h.update(leaf_prefix_bytes());
    hash_leaf_body(&mut h, leaf_input);
    h.finalize().to_vec()
}

pub fn node_digest(left: &[u8], right: &[u8]) -> Vec<u8> {
    let mut h = Sha256::new();
    h.update([0x01u8]);
    h.update(left);
    h.update(right);
    h.finalize().to_vec()
}

pub fn verify_inclusion(leaf_input: &str, root_hex: &str, path: &[ProofStep]) -> bool {
    let want = match hex::decode(root_hex) {
        Ok(v) => v,
        Err(_) => return false,
    };
    let mut acc = leaf_digest(leaf_input);
    for step in path {
        if step.side == "right" {
            acc = node_digest(&acc, &step.hash);
        } else {
            acc = node_digest(&step.hash, &acc);
        }
    }
    acc == want
}



