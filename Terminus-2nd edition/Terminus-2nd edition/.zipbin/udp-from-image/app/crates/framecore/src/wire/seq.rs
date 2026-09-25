/// Return true when `a` is before `b` in the active sequence space.
pub fn seq_before(a: u32, b: u32) -> bool {
    let a16 = (a & 0xFFFF) as u16;
    let b16 = (b & 0xFFFF) as u16;
    let diff = a16.wrapping_sub(b16);
    diff != 0 && diff < 0x8000
}

pub fn seq_after(a: u32, b: u32) -> bool {
    seq_before(b, a)
}

pub fn seq_le(a: u32, b: u32) -> bool {
    a == b || seq_before(a, b)
}
