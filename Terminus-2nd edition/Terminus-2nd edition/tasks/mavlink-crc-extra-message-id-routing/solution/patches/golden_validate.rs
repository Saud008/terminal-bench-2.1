use crate::crc::crc_v2;
use crate::error::{MavError, Result};
use crate::messages::{crc_extra, message_name};
use crate::model::{RawFrame, ValidatedFrame};

pub fn validate_frames(frames: Vec<RawFrame>) -> Result<Vec<ValidatedFrame>> {
    let mut out = Vec::new();
    for frame in frames {
        if !validate_one(&frame)? {
            continue;
        }
        out.push(ValidatedFrame {
            msg_id: frame.msg_id,
            name: message_name(frame.msg_id).to_string(),
            sysid: frame.sysid,
            compid: frame.compid,
            seq: frame.seq,
            payload: frame.payload,
        });
    }
    Ok(out)
}

fn validate_one(frame: &RawFrame) -> Result<bool> {
    let extra = crc_extra(frame.msg_id).ok_or_else(|| {
        MavError::Validate(format!("unknown msg_id {}", frame.msg_id))
    })?;
    let crc_input = build_crc_input(frame);
    let computed = crc_v2(&crc_input, extra);
    Ok(computed == frame.crc_wire)
}

fn build_crc_input(frame: &RawFrame) -> Vec<u8> {
    let mut out = Vec::with_capacity(9 + frame.payload.len());
    out.push(frame.header_len);
    out.push(frame.incompat);
    out.push(frame.compat);
    out.push(frame.seq);
    out.push(frame.sysid);
    out.push(frame.compid);
    // MAVLink v2 always includes all three little-endian msg_id bytes in the CRC.
    out.push((frame.msg_id & 0xFF) as u8);
    out.push(((frame.msg_id >> 8) & 0xFF) as u8);
    out.push(((frame.msg_id >> 16) & 0xFF) as u8);
    out.extend_from_slice(&frame.payload);
    out
}
