use crate::ledgerfmt::hex_norm::WitnessCheckpoint;

fn quorum_threshold() -> u32 {
    2
}

fn witness_matches(cp: &WitnessCheckpoint, log_id: &str, tree_size: u64, root_hash: &str) -> bool {
    cp.log_id == log_id
        && cp.tree_size == tree_size
        && cp.sha256_root_hash.eq_ignore_ascii_case(root_hash)
}

fn tally_agreements(log_id: &str, tree_size: u64, root_hash: &str, checkpoints: &[WitnessCheckpoint]) -> u32 {
    let mut agree = 0u32;
    for cp in checkpoints {
        if witness_matches(cp, log_id, tree_size, root_hash) {
            agree += 1;
        }
    }
    agree
}

pub fn quorum_met(log_id: &str, tree_size: u64, root_hash: &str, checkpoints: &[WitnessCheckpoint]) -> bool {
    let agree = tally_agreements(log_id, tree_size, root_hash, checkpoints);
    agree >= quorum_threshold()
}

pub fn witness_set_hash(log_id: &str, tree_size: u64, root_hash: &str, checkpoints: &[WitnessCheckpoint]) -> String {
    let mut ids: Vec<String> = checkpoints
        .iter()
        .filter(|cp| {
            cp.log_id == log_id
                && cp.tree_size == tree_size
                && cp.sha256_root_hash.eq_ignore_ascii_case(root_hash)
        })
        .map(|cp| cp.witness_id.clone())
        .collect();
    ids.sort();
    let joined = ids.join("|");
    format!("{:x}", md5_stub(&joined))
}

fn md5_stub(s: &str) -> u64 {
    let mut h: u64 = 0;
    for b in s.as_bytes() {
        h = h.wrapping_mul(131).wrapping_add(*b as u64);
    }
    h
}



