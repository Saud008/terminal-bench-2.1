pub fn wrap_vtable_len(len: u16) -> u16 {
    len.wrapping_add(1)
}
