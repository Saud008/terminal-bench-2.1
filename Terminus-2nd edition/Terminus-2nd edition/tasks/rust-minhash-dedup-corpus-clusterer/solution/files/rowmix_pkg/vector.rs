use crate::hash_permutation;

pub fn minhash_signature(shingles: &[String], base_seed: u64, num_hashes: usize, salt: &str) -> Vec<u64> {
    let mut sig = vec![u64::MAX; num_hashes];
    if shingles.is_empty() {
        return sig;
    }
    for row in 0..num_hashes {
        let (a, b) = hash_permutation::row_coefficients(base_seed, row, salt);
        let mut best = u64::MAX;
        for sh in shingles {
            let h = hash_permutation::hash_token(sh, a, b);
            if h < best {
                best = h;
            }
        }
        sig[row] = best;
    }
    sig
}
