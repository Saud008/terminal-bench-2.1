use crate::error::Result;
use crate::model::ValidatedFrame;
use std::collections::HashSet;

pub fn dedup_frames(
    frames: Vec<ValidatedFrame>,
    seen: &HashSet<(u8, u8, u32, u8)>,
) -> Result<(Vec<ValidatedFrame>, u32)> {
    let mut out = Vec::new();
    let mut local_seen = HashSet::new();
    let mut deduped = 0u32;
    for frame in frames {
        let key = (frame.sysid, frame.compid, frame.msg_id, frame.seq);
        if seen.contains(&key) || local_seen.contains(&key) {
            deduped += 1;
            continue;
        }
        local_seen.insert(key);
        out.push(frame);
    }
    Ok((out, deduped))
}
