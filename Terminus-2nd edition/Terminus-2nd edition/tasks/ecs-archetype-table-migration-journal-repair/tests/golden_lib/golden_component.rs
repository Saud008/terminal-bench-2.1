use std::collections::BTreeMap;

use sha2::{Digest, Sha256};

use crate::model::ComponentId;

fn seed_u64(seed: &str) -> u64 {
    let digest = Sha256::digest(seed.as_bytes());
    u64::from_le_bytes(digest[..8].try_into().expect("seed bytes"))
}

fn xorshift64(state: &mut u64) -> u64 {
    let mut x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    *state = x;
    x
}

pub fn registration_order(names: &[String], seed: &str) -> Vec<String> {
    let mut order = names.to_vec();
    let mut state = seed_u64(seed);
    for i in (1..order.len()).rev() {
        let j = (xorshift64(&mut state) as usize) % (i + 1);
        order.swap(i, j);
    }
    order
}

pub fn build_component_map(order: &[String]) -> BTreeMap<String, ComponentId> {
    order
        .iter()
        .enumerate()
        .map(|(idx, name)| (name.clone(), idx as ComponentId))
        .collect()
}
