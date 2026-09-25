use crate::errors::DecodeError;

pub fn strip_zlib_header(data: &[u8]) -> Result<&[u8], DecodeError> {
    if data.len() < 6 {
        return Err(DecodeError::Format("zlib stream too short".into()));
    }
    let cmf = data[0];
    let flg = data[1];
    if cmf & 0x0f != 8 {
        return Err(DecodeError::Format("unsupported compression method".into()));
    }
    if ((cmf as u16) << 8 | flg as u16) % 31 != 0 {
        return Err(DecodeError::Format("invalid zlib header check".into()));
    }
    let end = data.len().saturating_sub(4);
    if end < 2 {
        return Err(DecodeError::Format("missing adler trailer".into()));
    }
    Ok(&data[2..end])
}

pub fn read_zlib_adler(data: &[u8]) -> Result<u32, DecodeError> {
    if data.len() < 4 {
        return Err(DecodeError::Format("missing adler trailer".into()));
    }
    let trailer = &data[data.len() - 4..];
    Ok(u32::from_be_bytes([trailer[0], trailer[1], trailer[2], trailer[3]]))
}
