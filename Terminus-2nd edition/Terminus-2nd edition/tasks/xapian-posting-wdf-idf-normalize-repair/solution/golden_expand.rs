use std::collections::BTreeMap;

pub fn effective_wdf(
    term: &str,
    wdf: &BTreeMap<String, f64>,
    synonyms: &BTreeMap<String, Vec<String>>,
) -> f64 {
    let mut best = *wdf.get(term).unwrap_or(&0.0);
    if let Some(alts) = synonyms.get(term) {
        for alt in alts {
            best = best.max(*wdf.get(alt).unwrap_or(&0.0));
        }
    }
    best
}
