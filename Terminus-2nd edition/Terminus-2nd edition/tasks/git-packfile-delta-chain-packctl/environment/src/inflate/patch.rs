pub fn apply_patch(base: &[u8], patch_text: &[u8]) -> Result<Vec<u8>, String> {
    let text = std::str::from_utf8(patch_text).map_err(|e| e.to_string())?;
    let mut out = base.to_vec();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(rest) = line.strip_prefix("COPY ") {
            let parts: Vec<&str> = rest.split_whitespace().collect();
            if parts.len() != 2 {
                return Err(format!("bad COPY line: {line}"));
            }
            let offset: usize = parts[0].parse().map_err(|_| format!("bad offset: {line}"))?;
            let len: usize = parts[1].parse().map_err(|_| format!("bad len: {line}"))?;
            if offset + len > base.len() {
                return Err("COPY out of range".into());
            }
            out.extend_from_slice(&base[offset..offset + len]);
        } else if let Some(suffix) = line.strip_prefix("INSERT ") {
            out.extend_from_slice(suffix.as_bytes());
        } else {
            return Err(format!("unknown patch opcode: {line}"));
        }
    }
    Ok(out)
}
