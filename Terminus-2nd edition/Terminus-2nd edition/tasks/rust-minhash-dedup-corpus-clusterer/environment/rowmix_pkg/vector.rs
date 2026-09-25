use crate::hash_permutation;

pub fn minhash_signature(shingles: &[String], base_seed: u64, num_hashes: usize, salt: &str) -> Vec<u64> {
    let mut sig = vec![0u64; num_hashes];
    for row in 0..num_hashes {
        let (a, b) = hash_permutation::row_coefficients(base_seed, row, salt);
        let mut best = 0u64;
        for sh in shingles {
            let h = hash_permutation::hash_token(sh, a, b);
            if h > best {
                best = h;
            }
        }
        sig[row] = best;
    }
    sig
}
