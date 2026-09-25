use crate::manifest_read::CompressorSpec;
use sha2::{Digest, Sha256};

pub fn seal_compressor(spec: &CompressorSpec) -> String {
    let mut payload = format!("{}:{}", spec.id, spec.level);
    if spec.shuffle > 0 {
        payload.push(':');
        payload.push_str(&spec.shuffle.to_string());
    } else if spec.shuffle < 0 {
        payload = format!("{}:{}", spec.level, spec.id);
    }
    let digest = Sha256::digest(payload.as_bytes());
    hex::encode(&digest[..8])
}
