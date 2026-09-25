use crate::frame::{CapsuleFrame, Direction, SessionKey};
use std::fs;
use std::path::Path;

#[derive(Debug)]
pub struct CapsuleError;

const MAGIC: &[u8; 4] = b"CAPS";

pub fn read_capsule_dir(dir: &Path) -> Result<Vec<CapsuleFrame>, CapsuleError> {
    let mut frames = Vec::new();
    let mut paths: Vec<_> = fs::read_dir(dir).map_err(|_| CapsuleError)?.filter_map(|e| e.ok()).collect();
    paths.sort_by_key(|e| e.file_name());
    for entry in paths {
        let p = entry.path();
        if p.extension().and_then(|s| s.to_str()) != Some("pcap") {
            continue;
        }
        frames.extend(parse_capsule(&fs::read(&p).map_err(|_| CapsuleError)?)?);
    }
    frames.sort_by_key(|a| a.seq);
    Ok(frames)
}

fn parse_capsule(bytes: &[u8]) -> Result<Vec<CapsuleFrame>, CapsuleError> {
    if bytes.len() < 8 || &bytes[0..4] != MAGIC {
        return Err(CapsuleError);
    }
    let frame_count = u32::from_le_bytes(bytes[4..8].try_into().map_err(|_| CapsuleError)?);
    let mut off = 8usize;
    let mut out = Vec::new();
    for _ in 0..frame_count {
        if off + 16 > bytes.len() {
            return Err(CapsuleError);
        }
        let quad: [u8; 8] = bytes[off..off + 8].try_into().map_err(|_| CapsuleError)?;
        off += 8;
        let seq = u32::from_be_bytes(bytes[off..off + 4].try_into().map_err(|_| CapsuleError)?);
        off += 4;
        let dir_byte = bytes[off];
        off += 1;
        let direction = if dir_byte == 0 {
            Direction::Client
        } else {
            Direction::Server
        };
        let reflag = bytes[off];
        off += 1;
        let plen = u16::from_le_bytes(bytes[off..off + 2].try_into().map_err(|_| CapsuleError)?) as usize;
        off += 2;
        if off + plen > bytes.len() {
            return Err(CapsuleError);
        }
        let tls_payload = bytes[off..off + plen].to_vec();
        off += plen;
        out.push(CapsuleFrame {
            session: SessionKey { quad },
            seq,
            direction,
            tls_payload,
            is_retransmit: reflag == 0,
        });
    }
    Ok(out)
}
