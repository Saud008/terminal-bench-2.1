use std::collections::BTreeMap;

pub fn effective_wdf(
    term: &str,
    wdf: &BTreeMap<String, f64>,
    synonyms: &BTreeMap<String, Vec<String>>,
) -> f64 {
    let base = *wdf.get(term).unwrap_or(&0.0);
    let mut total = base;
    if let Some(alts) = synonyms.get(term) {
        for alt in alts {
            total += *wdf.get(alt).unwrap_or(&0.0);
        }
    }
    total
}
