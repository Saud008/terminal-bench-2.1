pub fn term_weight(
    effective_wdf: f64,
    idf: f64,
    cf: u64,
    rare_cf: u64,
    is_or: bool,
) -> f64 {
    if effective_wdf <= 0.0 {
        return 0.0;
    }
    if is_or && cf <= rare_cf {
        return effective_wdf;
    }
    effective_wdf * idf
}
