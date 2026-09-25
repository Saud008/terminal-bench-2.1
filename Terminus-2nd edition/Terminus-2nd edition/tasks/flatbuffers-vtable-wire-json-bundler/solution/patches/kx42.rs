use anyhow::{anyhow, bail, Result};

pub fn align_up(pos: usize, align: usize) -> usize {
    (pos + align - 1) & !(align - 1)
}

pub fn read_u16(buf: &[u8], pos: usize) -> Result<u16> {
    if pos + 2 > buf.len() {
        bail!("truncated u16 at {pos}");
    }
    Ok(u16::from_le_bytes([buf[pos], buf[pos + 1]]))
}

pub fn read_u32(buf: &[u8], pos: usize) -> Result<u32> {
    if pos + 4 > buf.len() {
        bail!("truncated u32 at {pos}");
    }
    Ok(u32::from_le_bytes([
        buf[pos],
        buf[pos + 1],
        buf[pos + 2],
        buf[pos + 3],
    ]))
}

pub fn read_i32(buf: &[u8], pos: usize) -> Result<i32> {
    if pos + 4 > buf.len() {
        bail!("truncated i32 at {pos}");
    }
    Ok(i32::from_le_bytes([
        buf[pos],
        buf[pos + 1],
        buf[pos + 2],
        buf[pos + 3],
    ]))
}

pub fn read_f32(buf: &[u8], pos: usize) -> Result<f32> {
    Ok(f32::from_le_bytes(read_u32(buf, pos)?.to_le_bytes()))
}

pub fn follow_uoffset(buf: &[u8], field_pos: usize) -> Result<usize> {
    let off = read_u32(buf, field_pos)? as usize;
    if off == 0 {
        return Err(anyhow!("null uoffset at {field_pos}"));
    }
    let target = field_pos + off;
    if target >= buf.len() {
        bail!("uoffset overflow at {field_pos}");
    }
    Ok(target)
}

pub fn root_table(buf: &[u8]) -> Result<usize> {
    if buf.len() < 4 {
        bail!("buffer too short for root offset");
    }
    let root_off = read_u32(buf, 0)? as usize;
    if root_off == 0 || root_off >= buf.len() {
        bail!("invalid root offset");
    }
    Ok(root_off)
}
