use crate::bitreader::BitReader;
use crate::errors::DecodeError;
use crate::window::Window;

pub fn stored_payload_checksum(payload: &[u8], len: u16, nlen: u16) -> u16 {
    let mut sum: u32 = 0;
    sum = sum.wrapping_add((len & 0xff) as u32);
    sum = sum.wrapping_add(((len >> 8) & 0xff) as u32);
    sum = sum.wrapping_add((nlen & 0xff) as u32);
    sum = sum.wrapping_add(((nlen >> 8) & 0xff) as u32);
    for &b in payload {
        sum = sum.wrapping_add(u32::from(b));
    }
    (sum & 0xffff) as u16
}

pub fn decode_stored_block(
    reader: &mut BitReader<'_>,
    window: &mut Window,
    out: &mut Vec<u8>,
) -> Result<(u16, u16), DecodeError> {
    reader.align_byte();
    let len = read_u16(reader)?;
    let nlen = read_u16(reader)?;
    if len != !nlen {
        return Err(DecodeError::Format(format!(
            "stored len/nlen mismatch {len}/{nlen}"
        )));
    }
    let data = reader
        .read_bytes(len as usize)
        .map_err(|_| DecodeError::Format("stored block truncated".into()))?;
    let checksum = stored_payload_checksum(data, len, nlen);
    window.extend(data, out);
    Ok((len, checksum))
}

fn read_u16(reader: &mut BitReader<'_>) -> Result<u16, DecodeError> {
    reader.align_byte();
    let bytes = reader
        .read_bytes(2)
        .map_err(|_| DecodeError::Format("unexpected eof reading u16".into()))?;
    Ok(u16::from_le_bytes([bytes[0], bytes[1]]))
}
