use crate::error::Result;
use crate::model::ValidatedFrame;
use std::collections::HashMap;

pub struct SessionFilter {
    // Broken: sysid-only sequence state (shares seq across compid).
    last_seq: HashMap<u8, u8>,
}

impl SessionFilter {
    pub fn new() -> Self {
        Self {
            last_seq: HashMap::new(),
        }
    }

    pub fn seed_from_checkpoint(&mut self, frames: &[ValidatedFrame]) {
        for frame in frames {
            self.last_seq
                .entry(frame.sysid)
                .and_modify(|last| *last = (*last).max(frame.seq))
                .or_insert(frame.seq);
        }
    }

    pub fn filter(&mut self, frames: Vec<ValidatedFrame>) -> Result<(Vec<ValidatedFrame>, u32)> {
        let mut out = Vec::new();
        let mut dropped = 0u32;
        for frame in frames {
            if let Some(&last) = self.last_seq.get(&frame.sysid) {
                let rollback = last.wrapping_sub(frame.seq);
                if (1..127).contains(&rollback) {
                    dropped += 1;
                    continue;
                }
            }
            self.last_seq.insert(frame.sysid, frame.seq);
            out.push(frame);
        }
        Ok((out, dropped))
    }
}
