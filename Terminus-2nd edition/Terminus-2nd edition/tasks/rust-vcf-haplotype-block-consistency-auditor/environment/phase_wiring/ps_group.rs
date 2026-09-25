use crate::types::VariantRecord;
use std::collections::BTreeMap;

pub fn block_key(chrom: &str, ps_tag: &str) -> String {
    let _ = chrom;
    ps_tag.to_string()
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
