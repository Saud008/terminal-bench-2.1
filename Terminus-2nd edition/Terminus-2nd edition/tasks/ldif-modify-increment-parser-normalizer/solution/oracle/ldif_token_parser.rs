use crate::error::{LdifError, Result};
use crate::model::{ChangeRecord, ChangeType, ModifyKind, ModifyOp};

pub fn parse_ldif(raw: &str) -> Result<Vec<ChangeRecord>> {
    let unfolded = unfold_lines(raw);
    let mut records = Vec::new();
    let mut block: Vec<String> = Vec::new();

    for line in unfolded {
        if line.trim().is_empty() {
            if !block.is_empty() {
                records.push(parse_block(&block)?);
                block.clear();
            }
            continue;
        }
        block.push(line);
    }
    if !block.is_empty() {
        records.push(parse_block(&block)?);
    }
    Ok(records)
}

pub fn unfold_lines(raw: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for line in raw.lines() {
        if line.starts_with(' ') {
            if let Some(last) = out.last_mut() {
                last.push_str(&line[1..]);
                continue;
            }
        }
        out.push(line.to_string());
    }
    out
}

fn parse_block(lines: &[String]) -> Result<ChangeRecord> {
    let mut dn = String::new();
    let mut changetype = None;
    let mut attributes: std::collections::BTreeMap<String, Vec<String>> =
        std::collections::BTreeMap::new();
    let mut modify_ops: Vec<ModifyOp> = Vec::new();
    let mut idx = 0usize;

    while idx < lines.len() {
        let line = &lines[idx];
        if line.trim() == "-" {
            idx += 1;
            continue;
        }
        let (key, value, base64) = split_line(line)?;
        let key_lower = key.to_ascii_lowercase();
        match key_lower.as_str() {
            "dn" if dn.is_empty() => dn = value,
            "changetype" if changetype.is_none() => {
                changetype = Some(parse_changetype(&value)?);
            }
            "-" => {
                idx += 1;
                continue;
            }
            _ => match changetype {
                Some(ChangeType::Modify) => {
                    if let Some(kind) = parse_modify_kind(&key_lower) {
                        let (op, consumed) = parse_modify_op(&lines[idx..], kind, &value)?;
                        modify_ops.push(op);
                        idx += consumed;
                        continue;
                    }
                }
                _ => {
                    let decoded = decode_value(base64, &value)?;
                    attributes
                        .entry(key_lower)
                        .or_default()
                        .push(decoded);
                }
            },
        }
        idx += 1;
    }

    let changetype = changetype.ok_or_else(|| LdifError::Parse("missing changetype".into()))?;
    if dn.is_empty() {
        return Err(LdifError::Parse("missing dn".into()));
    }

    Ok(ChangeRecord {
        dn,
        changetype,
        attributes,
        modify_ops,
    })
}

fn parse_modify_op(lines: &[String], kind: ModifyKind, attr_raw: &str) -> Result<(ModifyOp, usize)> {
    let attr = attr_raw.trim().to_ascii_lowercase();
    let mut values = Vec::new();
    let mut consumed = 1usize;
    while consumed < lines.len() {
        let line = &lines[consumed];
        if line.trim() == "-" {
            break;
        }
        let (key, value, base64) = split_line(line)?;
        if key.to_ascii_lowercase() != attr {
            break;
        }
        values.push(decode_value(base64, &value)?);
        consumed += 1;
    }
    Ok((
        ModifyOp {
            kind,
            attr,
            values,
        },
        consumed,
    ))
}

fn parse_modify_kind(key: &str) -> Option<ModifyKind> {
    match key {
        "add" => Some(ModifyKind::Add),
        "delete" => Some(ModifyKind::Delete),
        "replace" => Some(ModifyKind::Replace),
        _ => None,
    }
}

fn parse_changetype(value: &str) -> Result<ChangeType> {
    match value.to_ascii_lowercase().as_str() {
        "add" => Ok(ChangeType::Add),
        "modify" => Ok(ChangeType::Modify),
        "delete" => Ok(ChangeType::Delete),
        other => Err(LdifError::Parse(format!("unknown changetype: {other}"))),
    }
}

fn split_line(line: &str) -> Result<(String, String, bool)> {
    if let Some(pos) = line.find("::") {
        let key = line[..pos].trim().to_string();
        let value = line[pos + 2..].trim_start().to_string();
        return Ok((key, value, true));
    }
    if let Some(pos) = line.find(':') {
        let key = line[..pos].trim().to_string();
        let value = line[pos + 1..].trim_start().to_string();
        return Ok((key, value, false));
    }
    Err(LdifError::Parse(format!("invalid line: {line}")))
}

pub fn decode_value(base64: bool, value: &str) -> Result<String> {
    if !base64 {
        return Ok(value.to_string());
    }
    let mut padded = value.trim().to_string();
    while padded.len() % 4 != 0 {
        padded.push('=');
    }
    let bytes = base64::Engine::decode(
        &base64::engine::general_purpose::STANDARD,
        padded.as_bytes(),
    )
    .map_err(|err| LdifError::Parse(format!("base64: {err}")))?;
    String::from_utf8(bytes).map_err(|err| LdifError::Parse(format!("utf8: {err}")))
}
