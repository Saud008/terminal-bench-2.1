use capsule_io::CapsuleFrame;

pub fn dedupe_frames(frames: &[CapsuleFrame]) -> Vec<CapsuleFrame> {
    let mut seen = Vec::new();
    let mut out = Vec::new();
    for f in frames {
        let key = (f.session.quad, f.seq);
        if f.is_retransmit && seen.contains(&key) {
            continue;
        }
        seen.push(key);
        out.push(f.clone());
    }
    out
}
