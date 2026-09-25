use byteorder::{BigEndian, ByteOrder, LittleEndian, ReadBytesExt};
use std::io::Cursor;

use crate::errors::JitterError;
use crate::model::{PacketMeta, MAGIC_BE, MAGIC_LE};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct GlobalHeader {
    pub snaplen: u32,
    pub network: u32,
    pub big_endian: bool,
}

fn detect_endian(bytes: &[u8]) -> Result<bool, JitterError> {
    let le_magic = read_u32(bytes, 0, false);
    if le_magic == MAGIC_LE {
        let vmaj = read_u16(bytes, 4, false);
        let vmin = read_u16(bytes, 6, false);
        if vmaj == 2 && vmin == 4 {
            return Ok(false);
        }
    }
    let be_magic = read_u32(bytes, 0, true);
    if be_magic == MAGIC_BE {
        let vmaj = read_u16(bytes, 4, true);
        let vmin = read_u16(bytes, 6, true);
        if vmaj == 2 && vmin == 4 {
            return Ok(true);
        }
    }
    Err(JitterError::Parse(format!(
        "unsupported pcap magic le={le_magic:#x} be={be_magic:#x}"
    )))
}

fn read_u16(data: &[u8], off: usize, big_endian: bool) -> u16 {
    let mut cur = Cursor::new(&data[off..off + 2]);
    if big_endian {
        cur.read_u16::<BigEndian>().unwrap_or(0)
    } else {
        cur.read_u16::<LittleEndian>().unwrap_or(0)
    }
}

pub fn parse_savefile(bytes: &[u8]) -> Result<(GlobalHeader, Vec<PacketMeta>), JitterError> {
    if bytes.len() < 24 {
        return Err(JitterError::Parse("file too short for global header".into()));
    }
    let big_endian = detect_endian(bytes)?;
    let snaplen = read_u32(bytes, 16, big_endian);
    let network = read_u32(bytes, 20, big_endian);
    let mut offset = 24usize;
    let mut packets = Vec::new();
    let mut index = 0u32;
    while offset + 16 <= bytes.len() {
        let (ts_sec, ts_usec) = read_ts_fields(bytes, offset, big_endian);
        let incl_len = read_u32(bytes, offset + 8, big_endian);
        let orig_len = read_u32(bytes, offset + 12, big_endian);
        offset += 16;
        if offset + incl_len as usize > bytes.len() {
            return Err(JitterError::Parse("truncated packet payload".into()));
        }
        offset += incl_len as usize;
        let raw_ts_us = (ts_sec as u64) * 1_000_000 + ts_usec as u64;
        packets.push(PacketMeta {
            index,
            ts_sec,
            ts_usec,
            incl_len,
            orig_len,
            raw_ts_us,
        });
        index += 1;
    }
    Ok((
        GlobalHeader {
            snaplen,
            network,
            big_endian,
        },
        packets,
    ))
}

fn read_u32(data: &[u8], off: usize, big_endian: bool) -> u32 {
    let mut cur = Cursor::new(&data[off..off + 4]);
    if big_endian {
        cur.read_u32::<BigEndian>().unwrap_or(0)
    } else {
        cur.read_u32::<LittleEndian>().unwrap_or(0)
    }
}

pub fn read_ts_fields(data: &[u8], off: usize, big_endian: bool) -> (u32, u32) {
    let ts_sec = read_u32(data, off, big_endian);
    let ts_usec = read_u32(data, off + 4, big_endian);
    (ts_sec, ts_usec)
}
