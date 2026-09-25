pub fn encode_uint(value: u64) -> Vec<u8> {
    if value <= 23 {
        return vec![0x00 + value as u8];
    }
    if value <= 0xff {
        return vec![0x18, value as u8];
    }
    if value <= 0xffff {
        return vec![0x19, (value >> 8) as u8, value as u8];
    }
    if value <= 0xffff_ffff {
        return vec![
            0x1a,
            (value >> 24) as u8,
            (value >> 16) as u8,
            (value >> 8) as u8,
            value as u8,
        ];
    }
    vec![
        0x1b,
        (value >> 56) as u8,
        (value >> 48) as u8,
        (value >> 40) as u8,
        (value >> 32) as u8,
        (value >> 24) as u8,
        (value >> 16) as u8,
        (value >> 8) as u8,
        value as u8,
    ]
}

pub fn encode_text(text: &str) -> Vec<u8> {
    let bytes = text.as_bytes();
    let mut out = encode_text_header(bytes.len());
    out.extend_from_slice(bytes);
    out
}

pub fn encode_bytes(data: &[u8]) -> Vec<u8> {
    let mut out = encode_bytes_header(data.len());
    out.extend_from_slice(data);
    out
}

fn encode_text_header(len: usize) -> Vec<u8> {
    if len <= 23 {
        return vec![0x60 + len as u8];
    }
    if len <= 0xff {
        return vec![0x78, len as u8];
    }
    if len <= 0xffff {
        return vec![0x79, (len >> 8) as u8, len as u8];
    }
    vec![
        0x7a,
        (len >> 24) as u8,
        (len >> 16) as u8,
        (len >> 8) as u8,
        len as u8,
    ]
}

fn encode_bytes_header(len: usize) -> Vec<u8> {
    if len <= 23 {
        return vec![0x40 + len as u8];
    }
    if len <= 0xff {
        return vec![0x58, len as u8];
    }
    if len <= 0xffff {
        return vec![0x59, (len >> 8) as u8, len as u8];
    }
    vec![
        0x5a,
        (len >> 24) as u8,
        (len >> 16) as u8,
        (len >> 8) as u8,
        len as u8,
    ]
}

pub fn encode_array(items: &[Vec<u8>]) -> Vec<u8> {
    let mut out = encode_array_header(items.len());
    for item in items {
        out.extend_from_slice(item);
    }
    out
}

fn encode_array_header(len: usize) -> Vec<u8> {
    if len <= 23 {
        return vec![0x80 + len as u8];
    }
    if len <= 0xff {
        return vec![0x98, len as u8];
    }
    vec![0x99, (len >> 8) as u8, len as u8]
}

pub fn encode_map_pairs(pairs: &[(Vec<u8>, Vec<u8>)]) -> Vec<u8> {
    let mut out = encode_map_header(pairs.len());
    for (k, v) in pairs {
        out.extend_from_slice(k);
        out.extend_from_slice(v);
    }
    out
}

fn encode_map_header(len: usize) -> Vec<u8> {
    if len <= 23 {
        return vec![0xa0 + len as u8];
    }
    if len <= 0xff {
        return vec![0xb8, len as u8];
    }
    vec![0xb9, (len >> 8) as u8, len as u8]
}

pub fn decode_uint(data: &[u8], pos: &mut usize) -> Result<u64, String> {
    if *pos >= data.len() {
        return Err("unexpected end".into());
    }
    let initial = data[*pos];
    *pos += 1;
    let major = initial >> 5;
    let info = initial & 0x1f;
    if major != 0 {
        return Err("expected unsigned int".into());
    }
    match info {
        n @ 0..=23 => Ok(n as u64),
        24 => read_u8(data, pos).map(u64::from),
        25 => read_u16(data, pos).map(u64::from),
        26 => read_u32(data, pos).map(u64::from),
        27 => read_u64(data, pos),
        _ => Err("unsupported uint width".into()),
    }
}

pub fn decode_text(data: &[u8], pos: &mut usize) -> Result<String, String> {
    let bytes = decode_text_bytes(data, pos)?;
    String::from_utf8(bytes).map_err(|e| e.to_string())
}

fn decode_text_bytes(data: &[u8], pos: &mut usize) -> Result<Vec<u8>, String> {
    if *pos >= data.len() {
        return Err("unexpected end".into());
    }
    let initial = data[*pos];
    *pos += 1;
    let major = initial >> 5;
    let info = initial & 0x1f;
    if major != 3 {
        return Err("expected text string".into());
    }
    let len = match info {
        n @ 0..=23 => n as usize,
        24 => read_u8(data, pos)? as usize,
        25 => read_u16(data, pos)? as usize,
        26 => read_u32(data, pos)? as usize,
        27 => read_u64(data, pos)? as usize,
        _ => return Err("unsupported text string width".into()),
    };
    if *pos + len > data.len() {
        return Err("text string overruns input".into());
    }
    let out = data[*pos..*pos + len].to_vec();
    *pos += len;
    Ok(out)
}

pub fn decode_bytes(data: &[u8], pos: &mut usize) -> Result<Vec<u8>, String> {
    if *pos >= data.len() {
        return Err("unexpected end".into());
    }
    let initial = data[*pos];
    *pos += 1;
    let major = initial >> 5;
    let info = initial & 0x1f;
    if major != 2 {
        return Err("expected byte string".into());
    }
    let len = match info {
        n @ 0..=23 => n as usize,
        24 => read_u8(data, pos)? as usize,
        25 => read_u16(data, pos)? as usize,
        26 => read_u32(data, pos)? as usize,
        27 => read_u64(data, pos)? as usize,
        _ => return Err("unsupported byte string width".into()),
    };
    if *pos + len > data.len() {
        return Err("byte string overruns input".into());
    }
    let out = data[*pos..*pos + len].to_vec();
    *pos += len;
    Ok(out)
}

pub fn decode_array(data: &[u8], pos: &mut usize) -> Result<Vec<Vec<u8>>, String> {
    let len = decode_array_header(data, pos)?;
    let mut items = Vec::with_capacity(len);
    for _ in 0..len {
        let start = *pos;
        skip_value(data, pos)?;
        items.push(data[start..*pos].to_vec());
    }
    Ok(items)
}

pub fn decode_map(data: &[u8], pos: &mut usize) -> Result<Vec<(String, Vec<u8>)>, String> {
    let len = decode_map_header(data, pos)?;
    let mut pairs = Vec::with_capacity(len);
    for _ in 0..len {
        let key = decode_text(data, pos)?;
        let start = *pos;
        skip_value(data, pos)?;
        pairs.push((key, data[start..*pos].to_vec()));
    }
    Ok(pairs)
}

fn decode_array_header(data: &[u8], pos: &mut usize) -> Result<usize, String> {
    if *pos >= data.len() {
        return Err("unexpected end".into());
    }
    let initial = data[*pos];
    *pos += 1;
    let major = initial >> 5;
    let info = initial & 0x1f;
    if major != 4 {
        return Err("expected array".into());
    }
    match info {
        n @ 0..=23 => Ok(n as usize),
        24 => read_u8(data, pos).map(|v| v as usize),
        25 => read_u16(data, pos).map(|v| v as usize),
        _ => Err("unsupported array width".into()),
    }
}

fn decode_map_header(data: &[u8], pos: &mut usize) -> Result<usize, String> {
    if *pos >= data.len() {
        return Err("unexpected end".into());
    }
    let initial = data[*pos];
    *pos += 1;
    let major = initial >> 5;
    let info = initial & 0x1f;
    if major != 5 {
        return Err("expected map".into());
    }
    match info {
        n @ 0..=23 => Ok(n as usize),
        24 => read_u8(data, pos).map(|v| v as usize),
        25 => read_u16(data, pos).map(|v| v as usize),
        _ => Err("unsupported map width".into()),
    }
}

pub fn skip_value(data: &[u8], pos: &mut usize) -> Result<(), String> {
    if *pos >= data.len() {
        return Err("unexpected end".into());
    }
    let initial = data[*pos];
    let major = initial >> 5;
    let info = initial & 0x1f;
    match major {
        0 => {
            *pos += 1;
            if info >= 24 {
                let extra = 1 << (info - 24);
                *pos += extra;
            }
        }
        1 | 2 | 3 => {
            *pos += 1;
            let len = match info {
                n @ 0..=23 => n as usize,
                24 => read_u8(data, pos)? as usize,
                25 => read_u16(data, pos)? as usize,
                26 => read_u32(data, pos)? as usize,
                27 => read_u64(data, pos)? as usize,
                _ => return Err("unsupported length".into()),
            };
            *pos += len;
        }
        4 | 5 => {
            let count = if major == 4 {
                decode_array_header(data, pos)?
            } else {
                decode_map_header(data, pos)?
            };
            for _ in 0..count {
                if major == 5 {
                    skip_value(data, pos)?;
                }
                skip_value(data, pos)?;
            }
        }
        6 => {
            *pos += 1;
            if info >= 24 {
                let extra = 1 << (info - 24);
                *pos += extra;
            }
            skip_value(data, pos)?;
        }
        7 => {
            *pos += 1;
            if info >= 24 {
                let extra = 1 << (info - 24);
                *pos += extra;
            }
        }
        _ => return Err("unsupported major type".into()),
    }
    Ok(())
}

fn read_u8(data: &[u8], pos: &mut usize) -> Result<u8, String> {
    if *pos >= data.len() {
        return Err("unexpected end".into());
    }
    let v = data[*pos];
    *pos += 1;
    Ok(v)
}

fn read_u16(data: &[u8], pos: &mut usize) -> Result<u16, String> {
    if *pos + 2 > data.len() {
        return Err("unexpected end".into());
    }
    let v = u16::from_be_bytes([data[*pos], data[*pos + 1]]);
    *pos += 2;
    Ok(v)
}

fn read_u32(data: &[u8], pos: &mut usize) -> Result<u32, String> {
    if *pos + 4 > data.len() {
        return Err("unexpected end".into());
    }
    let v = u32::from_be_bytes([data[*pos], data[*pos + 1], data[*pos + 2], data[*pos + 3]]);
    *pos += 4;
    Ok(v)
}

fn read_u64(data: &[u8], pos: &mut usize) -> Result<u64, String> {
    if *pos + 8 > data.len() {
        return Err("unexpected end".into());
    }
    let mut buf = [0u8; 8];
    buf.copy_from_slice(&data[*pos..*pos + 8]);
    *pos += 8;
    Ok(u64::from_be_bytes(buf))
}
