use crate::model::RawFrame;

pub fn fnv1a64(input: &str) -> u64 {
    let mut h = 0xcbf29ce484222325_u64;
    for &b in input.as_bytes() {
        h ^= u64::from(b);
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

pub fn permute_frames(frames: &mut [RawFrame], seed: &str) {
    let mut order: Vec<usize> = (0..frames.len()).collect();
    order.sort_by_key(|idx| fnv1a64(&format!("{seed}:{idx}")));
    let original = frames.to_vec();
    for (i, &src) in order.iter().enumerate() {
        frames[i] = original[src].clone();
    }
}
