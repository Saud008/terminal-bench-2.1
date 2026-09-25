use crate::bytes::ByteReader;
use crate::error::DecodeError;

/// Read unsigned varint from the payload.
pub fn read_varint(reader: &mut ByteReader) -> Result<u32, DecodeError> {
    let mut value: u32 = 0;
    let mut shift = 0;
    loop {
        let b = reader.read_byte()?;
        value |= ((b & 0x7f) as u32) << shift;
        if b & 0x80 == 0 {
            return Ok(value);
        }
        shift += 7;
        if shift > 28 {
            return Err(DecodeError::InvalidVarint);
        }
    }
}

/// Encode-side helper for tests in Rust (not used by CLI).
pub fn write_varint(mut value: u32, out: &mut Vec<u8>) {
    loop {
        let mut byte = (value & 0x7f) as u8;
        value >>= 7;
        if value != 0 {
            byte |= 0x80;
        }
        out.push(byte);
        if value == 0 {
            break;
        }
    }
}
