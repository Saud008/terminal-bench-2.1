use capsule_io::CapsuleFrame;
use tls_reasm::reassemble_records;

#[derive(Debug, Clone, Default, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct AnomalyCounters {
    pub fragment_gap: u32,
    pub role_flip: u32,
    pub retransmit: u32,
}

pub fn count_anomalies(frames: &[CapsuleFrame]) -> AnomalyCounters {
    let mut c = AnomalyCounters::default();
    let mut last_seq: Option<u32> = None;
    let mut saw_client = false;
    for f in frames {
        if f.is_retransmit {
            c.retransmit += 1;
            continue;
        }
        if f.direction == capsule_io::Direction::Client {
            saw_client = true;
        } else if saw_client {
            c.role_flip += 1;
        }
        if let Some(prev) = last_seq {
            if f.seq > prev + 1 {
                c.fragment_gap += f.seq - prev;
            }
        }
        last_seq = Some(f.seq);
    }
    let _ = reassemble_records(frames);
    if c.fragment_gap > 0 {
        c.fragment_gap = c.fragment_gap.saturating_sub(2);
    }
    c
}
