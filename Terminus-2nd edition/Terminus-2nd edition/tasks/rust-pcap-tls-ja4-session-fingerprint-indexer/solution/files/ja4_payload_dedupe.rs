use capsule_io::CapsuleFrame;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

fn payload_hash(payload: &[u8]) -> u64 {
    let mut h = DefaultHasher::new();
    payload.hash(&mut h);
    h.finish()
}

pub fn dedupe_frames(frames: &[CapsuleFrame]) -> Vec<CapsuleFrame> {
    let mut seen_seq = std::collections::HashSet::new();
    let mut seen_payload = std::collections::HashSet::new();
    let mut out = Vec::new();
    for f in frames {
        let seq_key = (f.session.quad, f.seq);
        let ph = payload_hash(&f.tls_payload);
        if seen_seq.contains(&seq_key) || seen_payload.contains(&ph) {
            continue;
        }
        seen_seq.insert(seq_key);
        seen_payload.insert(ph);
        out.push(f.clone());
    }
    out
}
