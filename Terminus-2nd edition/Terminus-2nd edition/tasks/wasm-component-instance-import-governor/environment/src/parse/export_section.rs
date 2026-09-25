use crate::types::WireExport;
use crate::{EXPORT_KIND_FUNC, EXPORT_KIND_INSTANCE};

/// Decode exports from export section payload.
pub fn decode_exports(
    payload: &[u8],
    declared_len: u32,
    available: usize,
) -> Result<Vec<WireExport>, String> {
    let mut out = Vec::new();
    let mut pos = 0usize;
    while pos < payload.len() {
        if pos >= payload.len() {
            break;
        }
        let kind = payload[pos];
        pos += 1;
        if pos >= payload.len() {
            return Err("truncated export name len".into());
        }
        let nlen = payload[pos] as usize;
        pos += 1;
        if pos + nlen > payload.len() {
            return Err("truncated export name".into());
        }
        let name = std::str::from_utf8(&payload[pos..pos + nlen])
            .map_err(|e| e.to_string())?
            .to_string();
        pos += nlen;
        let instance_target = if kind == EXPORT_KIND_INSTANCE {
            if pos + 2 > payload.len() {
                return Err("truncated instance id".into());
            }
            let id = u16::from_le_bytes([payload[pos], payload[pos + 1]]);
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
    if (declared_len as usize) > available {
        return Err("export section declared length exceeds available bytes".into());
    }
    Ok(out)
}
