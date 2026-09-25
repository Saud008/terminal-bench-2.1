pub mod export_section;
pub mod type_index;

use crate::types::{ImportRow, ParsedComponent, ReexportEdge, TypeAlias};
use crate::CWRC_MAGIC;

pub use export_section::decode_exports;

pub fn parse_cwrc(filename: &str, raw: &[u8]) -> Result<ParsedComponent, String> {
    if raw.len() < 7 {
        return Err("cwrc too short".into());
    }
    if &raw[0..4] != CWRC_MAGIC {
        return Err("bad cwrc magic".into());
    }
    let version = raw[4];
    if version != 1 {
        return Err(format!("unsupported cwrc version {version}"));
    }
    let mut pos = 5usize;
    let import_count = read_u16(raw, &mut pos)?;
    let mut imports = Vec::with_capacity(import_count as usize);
    for _ in 0..import_count {
        imports.push(read_import(raw, &mut pos)?);
    }
    let alias_count = read_u16(raw, &mut pos)?;
    let mut aliases = Vec::with_capacity(alias_count as usize);
    for _ in 0..alias_count {
        aliases.push(TypeAlias {
            local: read_u16(raw, &mut pos)?,
            module_type: read_u16(raw, &mut pos)?,
        });
    }
    let (export_section_len, _leb_size) = read_leb128(raw, &mut pos)?;
    let payload_start = pos;
    let payload_end = payload_start
        .checked_add(export_section_len as usize)
        .ok_or("export section overflow")?;
    if payload_end > raw.len() {
        return Err("export section length exceeds file".into());
    }
    let exports = decode_exports(
        &raw[payload_start..payload_end],
        export_section_len,
        raw.len() - payload_start,
    )?;
    pos = payload_end;
    let reexport_count = read_u16(raw, &mut pos)?;
    let mut reexports = Vec::with_capacity(reexport_count as usize);
    for _ in 0..reexport_count {
        reexports.push(read_reexport(raw, &mut pos)?);
    }
    if pos != raw.len() {
        return Err(format!("trailing bytes {pos} != {}", raw.len()));
    }
    Ok(ParsedComponent {
        filename: filename.to_string(),
        raw: raw.to_vec(),
        imports,
        aliases,
        export_section_len,
        exports,
        reexports,
    })
}

fn read_import(raw: &[u8], pos: &mut usize) -> Result<ImportRow, String> {
    let mlen = read_u8(raw, pos)? as usize;
    let module = read_str(raw, pos, mlen)?;
    let nlen = read_u8(raw, pos)? as usize;
    let name = read_str(raw, pos, nlen)?;
    let type_local = read_u16(raw, pos)?;
    Ok(ImportRow {
        module,
        name,
        type_local,
    })
}

fn read_reexport(raw: &[u8], pos: &mut usize) -> Result<ReexportEdge, String> {
    let olen = read_u8(raw, pos)? as usize;
    let outer = read_str(raw, pos, olen)?;
    let via_instance = read_u16(raw, pos)?;
    let ilen = read_u8(raw, pos)? as usize;
    let inner = read_str(raw, pos, ilen)?;
    Ok(ReexportEdge {
        outer,
        via_instance,
        inner,
    })
}

pub fn read_u8(raw: &[u8], pos: &mut usize) -> Result<u8, String> {
    if *pos >= raw.len() {
        return Err("unexpected eof u8".into());
    }
    let v = raw[*pos];
    *pos += 1;
    Ok(v)
}

pub fn read_u16(raw: &[u8], pos: &mut usize) -> Result<u16, String> {
    if *pos + 2 > raw.len() {
        return Err("unexpected eof u16".into());
    }
    let v = u16::from_le_bytes([raw[*pos], raw[*pos + 1]]);
    *pos += 2;
    Ok(v)
}

pub fn read_str(raw: &[u8], pos: &mut usize, len: usize) -> Result<String, String> {
    if *pos + len > raw.len() {
        return Err("unexpected eof str".into());
    }
    let s = std::str::from_utf8(&raw[*pos..*pos + len])
        .map_err(|e| e.to_string())?
        .to_string();
    *pos += len;
    Ok(s)
}

pub fn read_leb128(raw: &[u8], pos: &mut usize) -> Result<(u32, usize), String> {
    let start = *pos;
    let mut result = 0u32;
    let mut shift = 0u32;
    for _ in 0..5 {
        let byte = read_u8(raw, pos)?;
        result |= ((byte & 0x7f) as u32) << shift;
        if byte & 0x80 == 0 {
            return Ok((result, *pos - start));
        }
        shift += 7;
        if shift > 35 {
            return Err("leb128 overflow".into());
        }
    }
    Err("leb128 unterminated".into())
}
