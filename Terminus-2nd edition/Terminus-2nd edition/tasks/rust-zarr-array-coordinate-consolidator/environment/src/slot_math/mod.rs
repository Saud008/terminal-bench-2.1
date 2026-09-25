use crate::manifest_read::ArrayManifest;

pub fn slot_count(manifest: &ArrayManifest) -> u64 {
    if manifest.shape.is_empty() || manifest.chunks.is_empty() {
        return 0;
    }
    let mut slots = 1u64;
    for (dim, chunk) in manifest.shape.iter().zip(manifest.chunks.iter()) {
        if *chunk == 0 {
            return 0;
        }
        slots *= dim / chunk;
    }
    slots
}
