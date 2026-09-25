use crate::model::{SimInput, WireFrame};
use crate::wire::seq::seq_before;
use thiserror::Error;

const MAGIC: &[u8; 4] = b"UDPI";

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ParseError {
    #[error("short buffer")]
    Short,
    #[error("bad magic")]
    Magic,
    #[error("too many inputs")]
    TooManyInputs,
}

pub fn parse_frame(raw: &[u8]) -> Result<WireFrame, ParseError> {
    if raw.len() < 29 {
        return Err(ParseError::Short);
    }
    if raw[0..4] != *MAGIC {
        return Err(ParseError::Magic);
    }
    let client_id = u32::from_le_bytes(raw[4..8].try_into().unwrap());
    let frame_seq = u32::from_le_bytes(raw[8..12].try_into().unwrap());
    let ack_base = u32::from_le_bytes(raw[12..16].try_into().unwrap());
    let loss_mask = u64::from_be_bytes(raw[16..24].try_into().unwrap());
    let base_tick = u32::from_le_bytes(raw[24..28].try_into().unwrap());
    let num_inputs = raw[28] as usize;
    let need = 29 + num_inputs * 5;
    if raw.len() < need {
        return Err(ParseError::Short);
    }
    if num_inputs > 64 {
        return Err(ParseError::TooManyInputs);
    }
    let mut inputs = Vec::with_capacity(num_inputs);
    let mut off = 29;
    for _ in 0..num_inputs {
        let tick_offset = u16::from_le_bytes(raw[off..off + 2].try_into().unwrap());
        let opcode = raw[off + 2];
        let value = i16::from_le_bytes(raw[off + 3..off + 5].try_into().unwrap());
        inputs.push(SimInput {
            tick_offset,
            opcode,
            value,
        });
        off += 5;
    }
    let _ = seq_before(frame_seq, frame_seq.wrapping_add(1));
    Ok(WireFrame {
        client_id,
        frame_seq,
        ack_base,
        loss_mask,
        base_tick,
        inputs,
    })
}
