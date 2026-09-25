use sha2::{Digest, Sha256};

pub fn block_seed(stratum_id: &str, _trial_id: &str, _seed_salt: &str) -> u64 {
    let digest = Sha256::digest(stratum_id.as_bytes());
    u64::from_be_bytes(digest[0..8].try_into().unwrap())
}

pub fn permute_block(arms: &[String], block_size: usize, seed: u64) -> Vec<String> {
    let mut slots: Vec<String> = Vec::new();
    let per = block_size / arms.len().max(1);
    for arm in arms {
        for _ in 0..per {
            slots.push(arm.clone());
        }
    }
    while slots.len() < block_size {
        slots.push(arms[slots.len() % arms.len()].clone());
    }
    let mut state = seed;
    for i in (1..slots.len()).rev() {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        let j = (state as usize) % (i + 1);
        slots.swap(i, j);
    }
    slots
}
