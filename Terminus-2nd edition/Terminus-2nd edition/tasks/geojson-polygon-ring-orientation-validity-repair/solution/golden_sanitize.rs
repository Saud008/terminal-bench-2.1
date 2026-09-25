use crate::types::Ring;

pub fn sanitize_ring(ring: Ring) -> (Ring, u32) {
    let mut removed = 0u32;
    if ring.is_empty() {
        return (ring, 0);
    }
    let mut out = vec![ring[0]];
    for p in ring.into_iter().skip(1) {
        if out.last().map(|q| q == &p).unwrap_or(false) {
            removed += 1;
            continue;
        }
        out.push(p);
    }
    (out, removed)
}
