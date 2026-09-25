use crate::bytes::ByteReader;
use crate::error::DecodeError;

pub fn read_varint(reader: &mut ByteReader) -> Result<u32, DecodeError> {
    let mut value: u32 = 0;
    let mut shift = 0;
    let mut raw: Vec<u8> = Vec::new();
    loop {
        let b = reader.read_byte()?;
        raw.push(b);
        value |= ((b & 0x7f) as u32) << shift;
        if b & 0x80 == 0 {
            if !is_canonical(&raw, value) {
                return Err(DecodeError::InvalidVarint);
            }
            return Ok(value);
        }
        shift += 7;
        if shift > 28 {
            return Err(DecodeError::InvalidVarint);
        }
    }
}

fn is_canonical(raw: &[u8], value: u32) -> bool {
    let mut expect = Vec::new();
    write_varint(value, &mut expect);
    raw == expect.as_slice()
}

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
