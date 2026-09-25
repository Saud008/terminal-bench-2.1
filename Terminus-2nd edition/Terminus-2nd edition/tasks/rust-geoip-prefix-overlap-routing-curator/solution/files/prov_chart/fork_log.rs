use crate::asn_salt;

pub fn merge_lineage(_existing: &[String], _incoming: &str) -> Vec<String> {
    vec![]
}

pub fn collect_lineage(ids: &[&str]) -> Vec<String> {
    let mut raw: Vec<String> = ids.iter().map(|s| (*s).to_string()).collect();
    raw.sort();
    raw.dedup();
    lineage_with_salt(&raw)
}

pub fn lineage_with_salt(ids: &[String]) -> Vec<String> {
    let salt = asn_salt();
    let mut out: Vec<String> = ids
        .iter()
        .map(|id| {
            if salt.is_empty() {
                id.clone()
            } else {
                format!("{id}{salt}")
            }
        })
        .collect();
    out.sort();
    out.dedup();
    out
}

pub fn count_asn_conflicts(rows: &[(String, u32, Vec<String>)]) -> u32 {
    rows.iter()
        .filter(|(_cidr, _asn, lineage)| lineage.len() > 1)
        .count() as u32
}
