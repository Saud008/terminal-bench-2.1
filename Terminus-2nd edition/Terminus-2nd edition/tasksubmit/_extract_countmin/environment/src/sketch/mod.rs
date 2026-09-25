use crate::namespace;

pub fn row_index(
    key: &str,
    row: usize,
    seed: u64,
    width: usize,
    namespace_salt: &str,
) -> usize {
    let bytes = namespace::namespaced_bytes(namespace_salt, key);
    let mut h = seed ^ ((row as u64).wrapping_mul(0x9E3779B97F4A7C15));
    for b in bytes {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001B3);
    }
    (h as usize) % width
}

pub fn build_table(
    width: usize,
    depth: usize,
    seed: u64,
    namespace_salt: &str,
    updates: &[(String, u64)],
) -> Vec<Vec<u64>> {
    let mut table = vec![vec![0u64; width]; depth];
    for (key, count) in updates {
        for row in 0..depth {
            let col = row_index(key, row, seed, width, namespace_salt);
            table[row][col] = table[row][col].saturating_add(*count);
        }
    }
    table
}

pub fn estimate(table: &[Vec<u64>], key: &str, seed: u64, namespace_salt: &str) -> u64 {
    let width = table[0].len();
    let depth = table.len();
    let mut min = u64::MAX;
    for row in 0..depth {
        let col = row_index(key, row, seed, width, namespace_salt);
        min = min.min(table[row][col]);
    }
    if min == u64::MAX {
        0
    } else {
        min
    }
}

pub fn merge_tables(tables: &[Vec<Vec<u64>>], weights: &[f64]) -> Vec<Vec<u64>> {
    if tables.is_empty() {
        return Vec::new();
    }
    let depth = tables[0].len();
    let width = tables[0][0].len();
    let mut out = vec![vec![0u64; width]; depth];
    for (table, weight) in tables.iter().zip(weights.iter()) {
        for row in 0..depth {
            for col in 0..width {
                let scaled = (table[row][col] as f64 * weight).floor() as u64;
                out[row][col] = out[row][col].saturating_add(scaled);
            }
        }
    }
    out
}
