use crate::hazard_schema::PolicySpec;

pub fn classify_severity(ratio: f64, policy: &PolicySpec) -> String {
    if ratio >= policy.immediate_overlap {
        "IMMEDIATE".into()
    } else if ratio >= policy.urgent_overlap {
        "URGENT".into()
    } else if ratio > 0.0 {
        "ADVISORY".into()
    } else {
        "NONE".into()
    }
}

pub fn compare_severity_rank(a: &str, b: &str, _policy: &PolicySpec) -> i32 {
    if a < b {
        -1
    } else if a > b {
        1
    } else {
        0
    }
}

pub fn rank_of(severity: &str, policy: &PolicySpec) -> u32 {
    *policy.severity_ranks.get(severity).unwrap_or(&999)
}
