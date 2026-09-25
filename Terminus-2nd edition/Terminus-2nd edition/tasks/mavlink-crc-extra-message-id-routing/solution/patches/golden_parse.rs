use crate::error::{MavError, Result};
use crate::model::RawFrame;

const STX_V2: u8 = 0xFD;

pub fn extract_frames(bytes: &[u8]) -> Result<Vec<RawFrame>> {
    let mut out = Vec::new();
    let mut idx = 0usize;
    while idx < bytes.len() {
        if bytes[idx] != STX_V2 {
            idx += 1;
            continue;
        }
        if idx + 10 > bytes.len() {
            break;
        }
        let header_len = bytes[idx + 1];
        let payload_len = usize::from(header_len);
        let frame_len = 10 + payload_len + 2;
        if idx + frame_len > bytes.len() {
            return Err(MavError::Parse("truncated frame".into()));
        }
        let msg_id = u32::from(bytes[idx + 7])
            | (u32::from(bytes[idx + 8]) << 8)
            | (u32::from(bytes[idx + 9]) << 16);
        let payload_start = idx + 10;
        let payload_end = payload_start + payload_len;
        let payload = bytes[payload_start..payload_end].to_vec();
        let crc_wire = u16::from(bytes[payload_end]) | (u16::from(bytes[payload_end + 1]) << 8);
        out.push(RawFrame {
            offset: idx,
            header_len,
            incompat: bytes[idx + 2],
            compat: bytes[idx + 3],
            seq: bytes[idx + 4],
            sysid: bytes[idx + 5],
            compid: bytes[idx + 6],
            msg_id,
            payload,
            crc_wire,
        });
        idx += frame_len;
    }
    Ok(out)
}
