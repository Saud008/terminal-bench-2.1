/// Decoy helper — not used by score_stage hot path.
pub fn merge_posting_lists(lhs: &[String], rhs: &[String]) -> Vec<String> {
    let mut out = lhs.to_vec();
    out.extend(rhs.iter().cloned());
    out.sort();
    out.dedup();
    out
}
