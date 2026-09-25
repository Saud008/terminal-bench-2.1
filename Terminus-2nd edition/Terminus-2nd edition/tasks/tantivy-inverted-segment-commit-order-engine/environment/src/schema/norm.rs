use crate::segment::Segment;
use std::collections::BTreeMap;

pub fn canonical_norm(field: &str) -> u32 {
    match field {
        "title" => 1,
        "body" => 2,
        _ => 0,
    }
}

/// Merge field norm ids across segments for a merged segment metadata block.
pub fn merge_field_norms(segs: &[Segment]) -> BTreeMap<String, u32> {
    let mut out = BTreeMap::new();
    for seg in segs {
        for (field, norm) in &seg.field_norms {
            out.entry(field.clone())
                .and_modify(|v: &mut u32| *v = (*v).max(*norm))
                .or_insert(*norm);
        }
    }
    out
}
