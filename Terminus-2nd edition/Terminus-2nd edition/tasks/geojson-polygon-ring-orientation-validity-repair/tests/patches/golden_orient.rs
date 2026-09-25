use crate::types::{PolygonCoords, Ring};
use crate::area::signed_area;

pub fn orient_polygon(rings: &mut PolygonCoords) -> (u32, u32) {
    let mut ext = 0u32;
    let mut intr = 0u32;
    for (idx, ring) in rings.iter_mut().enumerate() {
        let area = signed_area(ring);
        if idx == 0 {
            if area < 0.0 {
                reverse_ring(ring);
                ext += 1;
            }
        } else if area > 0.0 {
            reverse_ring(ring);
            intr += 1;
        }
    }
    (ext, intr)
}

fn reverse_ring(ring: &mut Ring) {
    ring.reverse();
}
