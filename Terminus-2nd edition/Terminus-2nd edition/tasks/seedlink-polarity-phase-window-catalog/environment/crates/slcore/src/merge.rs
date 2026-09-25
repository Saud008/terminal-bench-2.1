/// Legacy merge helper — not authoritative for catalog export.
pub fn merge_pick_lists(a: &[u16], b: &[u16]) -> Vec<u16> {
    let mut out = a.to_vec();
    out.extend_from_slice(b);
    out.sort_unstable();
    out.dedup();
    out
}
