use crate::parse::{OPT_EPB_CRC, OPT_END};

#[derive(Debug, Clone)]
pub struct EpbPacket {
    pub interface_id: u32,
    pub ts_ns: u64,
    pub cap_len: u32,
    pub packet_len: u32,
    pub crc_expected: Option<u32>,
}

pub fn parse_epb_body(body: &[u8]) -> Result<(EpbPacket, Vec<u8>), String> {
    if body.len() < 20 {
        return Err("epb body too short".into());
    }
    let interface_id = u32::from_le_bytes(body[0..4].try_into().unwrap());
    let ts_high = u32::from_le_bytes(body[4..8].try_into().unwrap());
    let ts_low = u32::from_le_bytes(body[8..12].try_into().unwrap());
    let cap_len = u32::from_le_bytes(body[12..16].try_into().unwrap());
    let packet_len = u32::from_le_bytes(body[16..20].try_into().unwrap());
    let cap = cap_len as usize;
    if body.len() < 20 + cap {
        return Err("epb truncated packet data".into());
    }
    let _packet_data = &body[20..20 + cap];
    let padded = (cap + 3) & !3;
    if body.len() < 20 + padded {
        return Err("epb padding overrun".into());
    }
    let core_end = 20 + padded;
    let core = &body[0..core_end];
    let mut crc_expected = None;
    let mut pos = core_end;
    while pos + 4 <= body.len() {
        let code = u16::from_le_bytes(body[pos..pos + 2].try_into().unwrap());
        let olen = u16::from_le_bytes(body[pos + 2..pos + 4].try_into().unwrap()) as usize;
        if code == OPT_END {
            break;
        }
        if pos + 4 + olen > body.len() {
            break;
        }
        let val = &body[pos + 4..pos + 4 + olen];
        if code == OPT_EPB_CRC && olen == 4 {
            crc_expected = Some(u32::from_le_bytes(val.try_into().unwrap()));
        }
        let opt_pad = (olen + 3) & !3;
        pos += 4 + opt_pad;
    }
    Ok((
        EpbPacket {
            interface_id,
            ts_ns: ((ts_high as u64) << 32) | ts_low as u64,
            cap_len,
            packet_len,
            crc_expected,
        },
        core.to_vec(),
    ))
}
