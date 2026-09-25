use std::fs;
use std::path::Path;

use crate::crc::compute_crc;
use crate::error::SlError;
use crate::message::{PickRow, SnippetMsg};

pub fn parse_file(path: &Path, enforce_invariant: bool) -> Result<SnippetMsg, SlError> {
    let raw = fs::read(path)?;
    if raw.len() < 30 {
        return Err(SlError::Parse("too short".to_string()));
    }
    if &raw[0..4] != b"SLWS" {
        return Err(SlError::Parse("bad magic".to_string()));
    }
    if raw[4] != 1 {
        return Err(SlError::Parse("bad version".to_string()));
    }
    let network = String::from_utf8_lossy(&raw[5..7]).to_string();
    let station = String::from_utf8_lossy(&raw[7..11])
        .trim_end_matches('\0')
        .to_string();
    let epoch_sec = u32::from_le_bytes(raw[11..15].try_into().unwrap());
    let leap_marker = raw[15];
    let sample_count = u16::from_le_bytes(raw[16..18].try_into().unwrap());
    let rate_mhz = u32::from_le_bytes(raw[18..22].try_into().unwrap());
    let body_polarity = raw[22] as i8;
    let mask_len = u16::from_le_bytes(raw[23..25].try_into().unwrap()) as usize;
    let mut off = 25;
    if off + mask_len > raw.len() {
        return Err(SlError::Parse("mask truncated".to_string()));
    }
    let clip_mask = raw[off..off + mask_len].to_vec();
    off += mask_len;
    let pick_count = raw[off] as usize;
    off += 1;
    let mut picks = Vec::with_capacity(pick_count);
    for _ in 0..pick_count {
        if off + 3 > raw.len() {
            return Err(SlError::Parse("pick truncated".to_string()));
        }
        picks.push(PickRow {
            sample_idx: u16::from_le_bytes(raw[off..off + 2].try_into().unwrap()),
            phase_code: raw[off + 2],
        });
        off += 3;
    }
    let sample_bytes = sample_count as usize * 2;
    if off + sample_bytes + 2 > raw.len() {
        return Err(SlError::Parse("samples truncated".to_string()));
    }
    let mut samples = Vec::with_capacity(sample_count as usize);
    for i in 0..sample_count as usize {
        let start = off + i * 2;
        samples.push(i16::from_le_bytes(raw[start..start + 2].try_into().unwrap()));
    }
    off += sample_bytes;
    let expected_crc = u16::from_le_bytes(raw[off..off + 2].try_into().unwrap());
    let actual_crc = compute_crc(&raw[..off]);
    if expected_crc != actual_crc {
        return Err(SlError::Parse("crc mismatch".to_string()));
    }
    if enforce_invariant && !crate::invariant::invariant_ok(&picks, sample_count) {
        return Err(SlError::Parse(
            "decode rejected snippet due to pick invariant".to_string(),
        ));
    }
    Ok(SnippetMsg {
        network,
        station,
        epoch_sec,
        leap_marker,
        sample_count,
        rate_mhz,
        body_polarity,
        clip_mask,
        picks,
        samples,
    })
}
