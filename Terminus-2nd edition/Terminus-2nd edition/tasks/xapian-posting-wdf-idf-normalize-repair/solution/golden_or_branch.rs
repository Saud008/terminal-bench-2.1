pub fn term_weight(
    effective_wdf: f64,
    idf: f64,
    _cf: u64,
    _rare_cf: u64,
    _is_or: bool,
) -> f64 {
    if effective_wdf <= 0.0 {
        return 0.0;
    }
    effective_wdf * idf
}
