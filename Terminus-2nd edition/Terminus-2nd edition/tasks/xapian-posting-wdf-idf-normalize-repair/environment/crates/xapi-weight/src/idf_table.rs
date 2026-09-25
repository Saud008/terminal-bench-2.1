/// Decoy IDF — score_stage computes IDF inline; editing this file alone does not fix queries.
pub fn idf_wrong(n: u64, cf: u64) -> f64 {
    if cf == 0 {
        return 0.0;
    }
    ((n as f64) / (cf as f64)).ln()
}
