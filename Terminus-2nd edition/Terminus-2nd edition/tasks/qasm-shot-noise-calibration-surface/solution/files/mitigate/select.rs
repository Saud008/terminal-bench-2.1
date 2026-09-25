use crate::types::MatrixCandidate;

pub fn select_matrix(
    candidates: &[MatrixCandidate],
    dimension: usize,
    seed_hash: &str,
    seed_offset: i32,
) -> MatrixCandidate {
    let prefix = if seed_offset != 0 {
        format!("{}:{}", &seed_hash[..6.min(seed_hash.len())], seed_offset)
    } else {
        seed_hash[..6.min(seed_hash.len())].to_string()
    };

    let mut matching: Vec<&MatrixCandidate> = candidates
        .iter()
        .filter(|c| c.dimension == dimension)
        .collect();
    matching.sort_by_key(|c| c.priority);
    matching.reverse();
    let max_pri = matching.first().map(|c| c.priority).unwrap_or(0);
    let tied: Vec<&MatrixCandidate> = matching
        .iter()
        .copied()
        .filter(|c| c.priority == max_pri)
        .collect();
    if tied.len() == 1 {
        return tied[0].clone();
    }
    let mut qualified: Vec<&MatrixCandidate> =
        tied.iter().copied().filter(|c| c.id >= prefix).collect();
    if qualified.is_empty() {
        qualified = tied;
    }
    qualified
        .iter()
        .min_by_key(|c| &c.id)
        .map(|c| (*c).clone())
        .unwrap()
}
