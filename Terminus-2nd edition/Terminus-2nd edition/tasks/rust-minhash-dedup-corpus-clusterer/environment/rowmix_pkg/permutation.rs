const PRIME: u64 = 1_000_000_007;

pub fn row_coefficients(base_seed: u64, row: usize, salt: &str) -> (u64, u64) {
    let mut seed = base_seed.wrapping_add(row as u64);
    if !salt.is_empty() {
        seed = seed.wrapping_add(salt.len() as u64);
    }
    let a = seed.wrapping_mul(6364136223846793005).wrapping_add(1) | 1;
    let b = seed.wrapping_add(1442695040888963407);
    (a % PRIME, b % PRIME)
}

pub fn hash_token(token: &str, a: u64, b: u64) -> u64 {
    let mut h: u64 = 0;
    for byte in token.as_bytes() {
        h = h.wrapping_mul(31).wrapping_add(u64::from(*byte));
    }
    (a.wrapping_mul(h).wrapping_add(b)) % PRIME
}
