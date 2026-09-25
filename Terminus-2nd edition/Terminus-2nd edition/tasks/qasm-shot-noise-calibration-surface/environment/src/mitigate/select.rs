use crate::types::MatrixCandidate;

pub fn select_matrix(
    candidates: &[MatrixCandidate],
    dimension: usize,
    _seed_hash: &str,
    _seed_offset: i32,
) -> MatrixCandidate {
    let max_pri = candidates
        .iter()
        .filter(|c| c.dimension == dimension)
        .map(|c| c.priority)
        .max()
        .unwrap_or(0);
    let picked = candidates
        .iter()
        .find(|c| c.dimension == dimension && c.priority == max_pri)
        .expect("matrix candidate");
    picked.clone()
}
