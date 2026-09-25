use std::fs;
use std::path::Path;

use crate::boundary::validate_boundaries;
use crate::crc::compute_crc;
use crate::error::FitError;
use crate::lap_time::read_lap_start_time;
use crate::message::LapMsg;

const MAGIC: &[u8; 4] = b"FITL";
const HEADER_LEN: usize = 6;
const CRC_LEN: usize = 2;
const NOTE_CAP: usize = 12;
const LAP_WIDTH: usize = 4 + 4 + 2 + 1 + 1 + NOTE_CAP;

pub fn parse_file(path: &Path, enforce_decode_alignment: bool) -> Result<Vec<LapMsg>, FitError> {
    let bytes = fs::read(path)?;
    if bytes.len() < HEADER_LEN + CRC_LEN {
        return Err(FitError::Parse("fit stream too short".to_string()));
    }
    if &bytes[0..4] != MAGIC {
        return Err(FitError::Parse("bad fit magic".to_string()));
    }
    let version = bytes[4];
    if version != 1 {
        return Err(FitError::Parse(format!("unsupported version {version}")));
    }
    let count = bytes[5] as usize;
    let payload_end = bytes.len() - CRC_LEN;
    let expected_crc = u16::from_le_bytes([bytes[payload_end], bytes[payload_end + 1]]);
    let actual_crc = compute_crc(&bytes[..payload_end]);
    if expected_crc != actual_crc {
        return Err(FitError::CrcMismatch {
            expected: expected_crc,
            actual: actual_crc,
        });
    }

    let payload = &bytes[HEADER_LEN..payload_end];
    if payload.len() != count * LAP_WIDTH {
        return Err(FitError::Parse("payload length does not match lap count".to_string()));
    }

    let mut laps = Vec::with_capacity(count);
    for idx in 0..count {
        let start = idx * LAP_WIDTH;
        let row = &payload[start..start + LAP_WIDTH];
        let start_time = read_lap_start_time(&row[0..4])?;
        let end_time = u32::from_le_bytes([row[4], row[5], row[6], row[7]]);
        let distance_m = u16::from_le_bytes([row[8], row[9]]);
        let trigger_code = row[10];
        let note_len = row[11] as usize;
        if note_len > NOTE_CAP {
            return Err(FitError::Parse("note length exceeds limit".to_string()));
        }
        let note_raw = &row[12..12 + note_len];
        let note = String::from_utf8(note_raw.to_vec())
            .map_err(|_| FitError::Parse("note is not valid utf-8".to_string()))?;
        let lap = LapMsg {
            original_index: idx,
            start_time,
            end_time,
            distance_m,
            trigger_code,
            note,
        };
        validate_boundaries(&lap, enforce_decode_alignment)?;
        laps.push(lap);
    }

    Ok(laps)
}
