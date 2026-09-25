/// Return true when `a` is before `b` in the active sequence space.
pub fn seq_before(a: u32, b: u32) -> bool {
    let diff = b.wrapping_sub(a);
    diff != 0 && diff < 0x8000_0000
}

pub fn seq_after(a: u32, b: u32) -> bool {
    seq_before(b, a)
}

pub fn seq_le(a: u32, b: u32) -> bool {
    a == b || seq_before(a, b)
}
