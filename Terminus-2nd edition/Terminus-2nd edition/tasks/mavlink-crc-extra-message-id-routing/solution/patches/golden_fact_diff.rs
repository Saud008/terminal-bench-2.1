use std::collections::{HashMap, HashSet};

use crate::error::{MavError, Result};
use crate::messages::{MSG_EVENT_LOG, MSG_GPS_RAW_INT};
use crate::model::{DiffRow, ValidatedFrame};

type FactKey = (u8, u8, u32, String);

pub fn compute_diff_rows(
    checkpoint_frames: &[ValidatedFrame],
    new_frames: &[ValidatedFrame],
) -> Result<Vec<DiffRow>> {
    let baseline = build_baseline(checkpoint_frames);
    let mut rows = Vec::new();
    let mut seen: HashSet<FactKey> = HashSet::new();

    for frame in new_frames {
        for (fact_key, new_value) in extract_fact_values(frame)? {
            let key = (frame.sysid, frame.compid, frame.msg_id, fact_key.clone());
            if seen.contains(&key) {
                continue;
            }
            if let Some(old_value) = baseline.get(&key) {
                if old_value != &new_value {
                    rows.push(DiffRow {
                        sysid: frame.sysid,
                        compid: frame.compid,
                        msg_id: frame.msg_id,
                        fact_key,
                        old_value: Some(old_value.clone()),
                        new_value,
                    });
                    seen.insert(key);
                }
            }
        }
    }

    rows.sort_by(|a, b| {
        (a.sysid, a.compid, a.msg_id, a.fact_key.as_str()).cmp(&(
            b.sysid,
            b.compid,
            b.msg_id,
            b.fact_key.as_str(),
        ))
    });
    Ok(rows)
}

fn build_baseline(frames: &[ValidatedFrame]) -> HashMap<FactKey, String> {
    let mut baseline = HashMap::new();
    for frame in frames {
        if let Ok(values) = extract_fact_values(frame) {
            for (fact_key, value) in values {
                let key = (frame.sysid, frame.compid, frame.msg_id, fact_key);
                baseline.insert(key, value);
            }
        }
    }
    baseline
}

fn extract_fact_values(frame: &ValidatedFrame) -> Result<Vec<(String, String)>> {
    let mut out = Vec::new();
    if frame.msg_id == MSG_GPS_RAW_INT {
        if frame.payload.len() < 12 {
            return Err(MavError::Route("gps payload too short".into()));
        }
        let time_boot_ms = u32::from_le_bytes(frame.payload[0..4].try_into().unwrap());
        let lat = i32::from_le_bytes(frame.payload[4..8].try_into().unwrap());
        let lon = i32::from_le_bytes(frame.payload[8..12].try_into().unwrap());
        out.push(("time_boot_ms".into(), stringify_scalar(&time_boot_ms)));
        out.push(("lat".into(), stringify_scalar(&lat)));
        out.push(("lon".into(), stringify_scalar(&lon)));
    } else if frame.msg_id == MSG_EVENT_LOG {
        if frame.payload.len() < 8 {
            return Err(MavError::Route("event payload too short".into()));
        }
        let timestamp_ms = u32::from_le_bytes(frame.payload[0..4].try_into().unwrap());
        let event_seq = u16::from_le_bytes(frame.payload[4..6].try_into().unwrap());
        let value = i16::from_le_bytes(frame.payload[6..8].try_into().unwrap());
        out.push(("timestamp_ms".into(), stringify_scalar(&timestamp_ms)));
        out.push(("event_seq".into(), stringify_scalar(&event_seq)));
        out.push(("value".into(), stringify_scalar(&value)));
    }
    Ok(out)
}

fn stringify_scalar<T: serde::Serialize>(value: &T) -> String {
    serde_json::to_string(value).unwrap_or_else(|_| "null".to_string())
}
