//! Non-authoritative export helper. Export must use publish/export on staged snapshots.

pub fn wrap_export_index(index: usize) -> u32 {
    index as u32
}
