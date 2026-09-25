use std::collections::HashMap;

pub fn active_site_counts(history: &[(String, String, bool)]) -> HashMap<String, u32> {
    let mut counts: HashMap<String, u32> = HashMap::new();
    for (site, _subject, _active) in history {
        *counts.entry(site.clone()).or_insert(0) += 1;
    }
    counts
}

pub fn venues_at_cap(counts: &HashMap<String, u32>, caps: &HashMap<String, u32>) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for (site, cap) in caps {
        if counts.get(site).copied().unwrap_or(0) >= *cap {
            out.push(site.clone());
        }
    }
    out.sort();
    out
}
