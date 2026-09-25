use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

pub fn fingerprint(buf: &[u8], revision: u32) -> String {
    let mut hasher = DefaultHasher::new();
    buf.len().hash(&mut hasher);
    if buf.len() >= 4 {
        buf[0..4].hash(&mut hasher);
    }
    revision.hash(&mut hasher);
    format!("{:016x}", hasher.finish())
}
