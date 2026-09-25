use sha2::{Digest, Sha256};

#[derive(Debug, Clone)]
pub struct ProofStep {
    pub hash: Vec<u8>,
    pub side: String,
}

pub fn leaf_digest(leaf_input: &str) -> Vec<u8> {
    let mut h = Sha256::new();
    h.update([0x01u8]);
    h.update(leaf_input.as_bytes());
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



