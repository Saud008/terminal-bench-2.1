pub fn escape(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 8);
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out
}

pub fn string_array(items: &[String]) -> String {
    let parts: Vec<String> = items
        .iter()
        .map(|s| format!("\"{}\"", escape(s)))
        .collect();
    format!("[{}]", parts.join(","))
}

/// Extract a JSON string array for a top-level key like "pins".
pub fn extract_string_array(raw: &str, key: &str) -> Result<Vec<String>, String> {
    let needle = format!("\"{}\"", key);
    let start = raw
        .find(&needle)
        .ok_or_else(|| format!("missing key {key}"))?;
    let after = &raw[start + needle.len()..];
    let bracket = after
        .find('[')
        .ok_or_else(|| format!("missing array for {key}"))?;
    let mut i = bracket + 1;
    let bytes = after.as_bytes();
    let mut out = Vec::new();
    while i < bytes.len() {
        while i < bytes.len() && ((bytes[i] as char).is_whitespace() || bytes[i] == b',') {
            i += 1;
        }
        if i < bytes.len() && bytes[i] == b']' {
            break;
        }
        if i >= bytes.len() || bytes[i] != b'"' {
            return Err(format!("bad string in {key}"));
        }
        i += 1;
        let mut s = String::new();
        while i < bytes.len() {
            let c = bytes[i];
            if c == b'\\' {
                i += 1;
                if i >= bytes.len() {
                    return Err("bad escape".into());
                }
                s.push(bytes[i] as char);
                i += 1;
                continue;
            }
            if c == b'"' {
                i += 1;
                break;
            }
            s.push(c as char);
            i += 1;
        }
        out.push(s);
    }
    Ok(out)
}

pub fn extract_usize(raw: &str, key: &str) -> Result<usize, String> {
    let needle = format!("\"{}\"", key);
    let start = raw
        .find(&needle)
        .ok_or_else(|| format!("missing key {key}"))?;
    let after = &raw[start + needle.len()..];
    let colon = after
        .find(':')
        .ok_or_else(|| format!("missing colon for {key}"))?;
    let mut i = colon + 1;
    let bytes = after.as_bytes();
    while i < bytes.len() && (bytes[i] as char).is_whitespace() {
        i += 1;
    }
    let begin = i;
    while i < bytes.len() && (bytes[i] as char).is_ascii_digit() {
        i += 1;
    }
    after[begin..i]
        .parse::<usize>()
        .map_err(|e| e.to_string())
}
