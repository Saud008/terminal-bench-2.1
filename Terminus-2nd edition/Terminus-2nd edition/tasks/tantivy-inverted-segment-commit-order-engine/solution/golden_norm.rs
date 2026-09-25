use crate::segment::Segment;
use std::collections::BTreeMap;

pub fn canonical_norm(field: &str) -> u32 {
    match field {
        "title" => 1,
        "body" => 2,
        _ => 0,
    }
}

pub fn merge_field_norms(_segs: &[Segment]) -> BTreeMap<String, u32> {
    let mut out = BTreeMap::new();
    out.insert("title".to_string(), canonical_norm("title"));
    out.insert("body".to_string(), canonical_norm("body"));
    out
}
