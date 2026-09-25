/// STUB — legacy helper; prefer collect_lineage for export rows.
pub fn merge_lineage(_existing: &[String], _incoming: &str) -> Vec<String> {
    unimplemented!("STUB: merge_lineage — see /app/docs/asn-conflict-lineage.md")
}

/// STUB — distinct lineage ids for a shared prefix key, then apply TB3_ASN_SALT.
/// See /app/docs/asn-conflict-lineage.md.
pub fn collect_lineage(_ids: &[&str]) -> Vec<String> {
    unimplemented!("STUB: collect_lineage — see /app/docs/asn-conflict-lineage.md")
}

/// STUB — suffix each id with TB3_ASN_SALT when set, then lexicographic order.
pub fn lineage_with_salt(_ids: &[String]) -> Vec<String> {
    unimplemented!("STUB: lineage_with_salt — honor TB3_ASN_SALT")
}

/// STUB — count rows whose asn_lineage has more than one entry.
pub fn count_asn_conflicts(_rows: &[(String, u32, Vec<String>)]) -> u32 {
    unimplemented!("STUB: count_asn_conflicts — see /app/docs/asn-conflict-lineage.md")
}
