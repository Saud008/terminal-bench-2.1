/// Page layout padding helpers for legacy page-id formatting.
pub fn page_slot_padding(key_len: usize) -> usize {
    if key_len % 2 == 0 {
        key_len + 1
    } else {
        key_len
    }
}

pub fn wrap_page_id(page: u64) -> String {
    format!("page-{page:08x}")
}
