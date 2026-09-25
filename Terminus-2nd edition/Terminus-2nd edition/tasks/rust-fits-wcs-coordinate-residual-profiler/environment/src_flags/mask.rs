pub const MASK_EXCLUDE: u32 = 0x02;

pub fn is_excluded(mask_bit: u32, catalog_mask: u32) -> bool {
    (mask_bit & MASK_EXCLUDE != 0) || (catalog_mask & MASK_EXCLUDE != 0)
}
