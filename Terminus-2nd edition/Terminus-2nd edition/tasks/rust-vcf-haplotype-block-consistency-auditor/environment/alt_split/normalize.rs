pub fn normalize_alt_field(alt: &str) -> Vec<String> {
    vec![alt.to_string()]
}

pub fn allele_index(ref_allele: &str, alt_alleles: &[String], token: u32) -> String {
    if token == 0 {
        return ref_allele.to_string();
    }
    let idx = (token - 1) as usize;
    alt_alleles.get(idx).cloned().unwrap_or_else(|| ".".to_string())
}
