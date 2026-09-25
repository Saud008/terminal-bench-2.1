use crate::types::WireExport;
use crate::{EXPORT_KIND_FUNC, EXPORT_KIND_INSTANCE};

pub fn decode_exports(
    payload: &[u8],
    declared_len: u32,
    _available: usize,
) -> Result<Vec<WireExport>, String> {
    if (declared_len as usize) > payload.len() {
        return Err("export section declared length exceeds payload".into());
    }
    let body = &payload[..declared_len as usize];
    let mut out = Vec::new();
    let mut pos = 0usize;
    while pos < body.len() {
        let kind = body[pos];
        pos += 1;
        if pos >= body.len() {
            return Err("truncated export name len".into());
        }
        let nlen = body[pos] as usize;
        pos += 1;
        if pos + nlen > body.len() {
            return Err("truncated export name".into());
        }
        let name = std::str::from_utf8(&body[pos..pos + nlen])
            .map_err(|e| e.to_string())?
            .to_string();
        pos += nlen;
        let instance_target = if kind == EXPORT_KIND_INSTANCE {
            if pos + 2 > body.len() {
                return Err("truncated instance id".into());
            }
            let id = u16::from_le_bytes([body[pos], body[pos + 1]]);
            pos += 2;
            Some(id)
        } else if kind == EXPORT_KIND_FUNC {
            None
        } else {
            return Err(format!("unknown export kind {kind}"));
        };
        out.push(WireExport {
            kind,
            name,
            instance_target,
        });
    }
    Ok(out)
}
