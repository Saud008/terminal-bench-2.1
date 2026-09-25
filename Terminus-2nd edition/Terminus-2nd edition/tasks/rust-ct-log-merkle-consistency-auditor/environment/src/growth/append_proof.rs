use crate::ctpath::leaf_body::{node_digest, ProofStep};

pub fn verify_consistency(from_root_hex: &str, to_root_hex: &str, from_size: u64, to_size: u64, path: &[ProofStep]) -> bool {
    if from_size >= to_size {
        return false;
    }
    let from_root = match hex::decode(from_root_hex) {
        Ok(v) => v,
        Err(_) => return false,
    };
    let to_root = match hex::decode(to_root_hex) {
        Ok(v) => v,
        Err(_) => return false,
    };
    let mut acc = from_root;
    for step in path {
        if step.side == "right" {
            acc = node_digest(&acc, &step.hash);
        } else {
            acc = node_digest(&step.hash, &acc);
        }
    }
    acc == to_root
}
