use crate::types::Ring;

pub fn normalize_close(ring: Ring) -> (Ring, u32) {
    if ring.is_empty() {
        return (ring, 0);
    }
    let mut normalized = 0u32;
    let mut out = ring;
    while out.len() > 1 && out.first() == out.last() {
        out.pop();
        normalized += 1;
    }
    if !out.is_empty() {
        let first = out[0];
        if out.last() != Some(&first) {
            out.push(first);
            normalized += 1;
        }
    }
    (out, normalized)
}
