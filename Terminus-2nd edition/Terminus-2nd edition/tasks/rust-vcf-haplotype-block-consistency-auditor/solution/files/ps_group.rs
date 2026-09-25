use crate::types::VariantRecord;
use std::collections::BTreeMap;

pub fn normalize_ps(ps_tag: &str) -> String {
    if let Ok(salt) = std::env::var("TB3_PS_SALT") {
        if !salt.is_empty() && ps_tag.starts_with(&salt) {
            let rest = &ps_tag[salt.len()..];
            return rest.trim_start_matches('-').to_string();
        }
    }
    ps_tag.to_string()
}

pub fn block_key(chrom: &str, ps_tag: &str) -> String {
    format!("{}:{}", chrom, normalize_ps(ps_tag))
}

pub fn group_variants(variants: &[VariantRecord]) -> BTreeMap<String, Vec<&VariantRecord>> {
    let mut groups: BTreeMap<String, Vec<&VariantRecord>> = BTreeMap::new();
    for v in variants {
        for gt in &v.genotypes {
            if gt.ps_tag.is_empty() {
                continue;
            }
            let key = block_key(&v.chrom, &gt.ps_tag);
            groups.entry(key).or_default().push(v);
        }
    }
    groups
}
