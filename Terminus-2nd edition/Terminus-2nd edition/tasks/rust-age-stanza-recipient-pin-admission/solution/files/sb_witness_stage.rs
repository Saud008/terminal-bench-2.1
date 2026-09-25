use crate::parse::header_scan::{ParsedFile, Stanza};
use std::fs;
use std::path::Path;

pub fn write_witness(path: &Path, files: &[ParsedFile]) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let mut sorted = files.to_vec();
    sorted.sort_by(|a, b| a.file_id.cmp(&b.file_id));
    let parts: Vec<String> = sorted.iter().map(|f| f.to_json()).collect();
    let mut body = format!("{{\"files\":[{}]}}", parts.join(","));
    body.push('\n');
    fs::write(path, body).map_err(|e| e.to_string())
}

pub fn read_witness(path: &Path) -> Result<Vec<ParsedFile>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let value = json_value::parse(&raw)?;
    let files_val = value.get("files").ok_or_else(|| "missing files".to_string())?;
    let arr = files_val
        .as_array()
        .ok_or_else(|| "files not array".to_string())?;
    let mut out = Vec::new();
    for item in arr {
        let file_id = item
            .get("file_id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        let rel_path = item
            .get("rel_path")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        let parse_ok = item.get("parse_ok").and_then(|v| v.as_bool()).unwrap_or(false);
        let mut stanzas = Vec::new();
        if let Some(st_arr) = item.get("stanzas").and_then(|v| v.as_array()) {
            for st in st_arr {
                let type_name = st
                    .get("type")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();
                let args = st
                    .get("args")
                    .and_then(|v| v.as_array())
                    .map(|a| {
                        a.iter()
                            .filter_map(|x| x.as_str().map(|s| s.to_string()))
                            .collect()
                    })
                    .unwrap_or_default();
                let fingerprint = st
                    .get("fingerprint")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();
                stanzas.push(Stanza {
                    type_name,
                    args,
                    fingerprint,
                });
            }
        }
        out.push(ParsedFile {
            file_id,
            rel_path,
            parse_ok,
            stanzas,
        });
    }
    Ok(out)
}

/// Minimal recursive-descent JSON reader, tolerant of both pretty-printed and
/// compact whitespace, sufficient for parsing witness/ledger shaped documents
/// without a `serde_json` dependency.
mod json_value {
    #[allow(dead_code)]
    pub enum JsonValue {
        Null,
        Bool(bool),
        Num(f64),
        Str(String),
        Array(Vec<JsonValue>),
        Object(Vec<(String, JsonValue)>),
    }

    impl JsonValue {
        pub fn get(&self, key: &str) -> Option<&JsonValue> {
            match self {
                JsonValue::Object(pairs) => pairs.iter().find(|(k, _)| k == key).map(|(_, v)| v),
                _ => None,
            }
        }

        pub fn as_str(&self) -> Option<&str> {
            match self {
                JsonValue::Str(s) => Some(s),
                _ => None,
            }
        }

        pub fn as_bool(&self) -> Option<bool> {
            match self {
                JsonValue::Bool(b) => Some(*b),
                _ => None,
            }
        }

        pub fn as_array(&self) -> Option<&Vec<JsonValue>> {
            match self {
                JsonValue::Array(a) => Some(a),
                _ => None,
            }
        }
    }

    pub fn parse(input: &str) -> Result<JsonValue, String> {
        let bytes = input.as_bytes();
        let mut pos = 0usize;
        skip_ws(bytes, &mut pos);
        parse_value(bytes, &mut pos)
    }

    fn skip_ws(bytes: &[u8], pos: &mut usize) {
        while *pos < bytes.len() && (bytes[*pos] as char).is_whitespace() {
            *pos += 1;
        }
    }

    fn parse_value(bytes: &[u8], pos: &mut usize) -> Result<JsonValue, String> {
        skip_ws(bytes, pos);
        if *pos >= bytes.len() {
            return Err("unexpected end of input".to_string());
        }
        match bytes[*pos] {
            b'{' => parse_object(bytes, pos),
            b'[' => parse_array(bytes, pos),
            b'"' => parse_string(bytes, pos).map(JsonValue::Str),
            b't' | b'f' => parse_bool(bytes, pos),
            b'n' => parse_null(bytes, pos),
            _ => parse_number(bytes, pos),
        }
    }

    fn parse_object(bytes: &[u8], pos: &mut usize) -> Result<JsonValue, String> {
        *pos += 1;
        let mut pairs = Vec::new();
        skip_ws(bytes, pos);
        if *pos < bytes.len() && bytes[*pos] == b'}' {
            *pos += 1;
            return Ok(JsonValue::Object(pairs));
        }
        loop {
            skip_ws(bytes, pos);
            if *pos >= bytes.len() || bytes[*pos] != b'"' {
                return Err("expected string key".to_string());
            }
            let key = parse_string(bytes, pos)?;
            skip_ws(bytes, pos);
            if *pos >= bytes.len() || bytes[*pos] != b':' {
                return Err("expected colon".to_string());
            }
            *pos += 1;
            let value = parse_value(bytes, pos)?;
            pairs.push((key, value));
            skip_ws(bytes, pos);
            if *pos >= bytes.len() {
                return Err("unexpected end in object".to_string());
            }
            match bytes[*pos] {
                b',' => {
                    *pos += 1;
                    continue;
                }
                b'}' => {
                    *pos += 1;
                    break;
                }
                _ => return Err("expected , or }".to_string()),
            }
        }
        Ok(JsonValue::Object(pairs))
    }

    fn parse_array(bytes: &[u8], pos: &mut usize) -> Result<JsonValue, String> {
        *pos += 1;
        let mut items = Vec::new();
        skip_ws(bytes, pos);
        if *pos < bytes.len() && bytes[*pos] == b']' {
            *pos += 1;
            return Ok(JsonValue::Array(items));
        }
        loop {
            let value = parse_value(bytes, pos)?;
            items.push(value);
            skip_ws(bytes, pos);
            if *pos >= bytes.len() {
                return Err("unexpected end in array".to_string());
            }
            match bytes[*pos] {
                b',' => {
                    *pos += 1;
                    continue;
                }
                b']' => {
                    *pos += 1;
                    break;
                }
                _ => return Err("expected , or ]".to_string()),
            }
        }
        Ok(JsonValue::Array(items))
    }

    fn parse_string(bytes: &[u8], pos: &mut usize) -> Result<String, String> {
        if bytes[*pos] != b'"' {
            return Err("expected string".to_string());
        }
        *pos += 1;
        let mut buf: Vec<u8> = Vec::new();
        while *pos < bytes.len() {
            let c = bytes[*pos];
            if c == b'"' {
                *pos += 1;
                return Ok(String::from_utf8_lossy(&buf).into_owned());
            }
            if c == b'\\' {
                *pos += 1;
                if *pos >= bytes.len() {
                    return Err("bad escape".to_string());
                }
                match bytes[*pos] {
                    b'"' => buf.push(b'"'),
                    b'\\' => buf.push(b'\\'),
                    b'/' => buf.push(b'/'),
                    b'n' => buf.push(b'\n'),
                    b't' => buf.push(b'\t'),
                    b'r' => buf.push(b'\r'),
                    b'b' => buf.push(0x08),
                    b'f' => buf.push(0x0c),
                    b'u' => {
                        if *pos + 4 >= bytes.len() {
                            return Err("bad unicode escape".to_string());
                        }
                        let hex = std::str::from_utf8(&bytes[*pos + 1..*pos + 5])
                            .map_err(|e| e.to_string())?;
                        let code = u32::from_str_radix(hex, 16).map_err(|e| e.to_string())?;
                        if let Some(ch) = char::from_u32(code) {
                            let mut tmp = [0u8; 4];
                            let s = ch.encode_utf8(&mut tmp);
                            buf.extend_from_slice(s.as_bytes());
                        }
                        *pos += 4;
                    }
                    other => buf.push(other),
                }
                *pos += 1;
                continue;
            }
            buf.push(c);
            *pos += 1;
        }
        Err("unterminated string".to_string())
    }

    fn parse_bool(bytes: &[u8], pos: &mut usize) -> Result<JsonValue, String> {
        if bytes[*pos..].starts_with(b"true") {
            *pos += 4;
            Ok(JsonValue::Bool(true))
        } else if bytes[*pos..].starts_with(b"false") {
            *pos += 5;
            Ok(JsonValue::Bool(false))
        } else {
            Err("bad literal".to_string())
        }
    }

    fn parse_null(bytes: &[u8], pos: &mut usize) -> Result<JsonValue, String> {
        if bytes[*pos..].starts_with(b"null") {
            *pos += 4;
            Ok(JsonValue::Null)
        } else {
            Err("bad literal".to_string())
        }
    }

    fn parse_number(bytes: &[u8], pos: &mut usize) -> Result<JsonValue, String> {
        let start = *pos;
        if *pos < bytes.len() && (bytes[*pos] == b'-' || bytes[*pos] == b'+') {
            *pos += 1;
        }
        while *pos < bytes.len()
            && (bytes[*pos].is_ascii_digit()
                || bytes[*pos] == b'.'
                || bytes[*pos] == b'e'
                || bytes[*pos] == b'E'
                || bytes[*pos] == b'-'
                || bytes[*pos] == b'+')
        {
            *pos += 1;
        }
        let s = std::str::from_utf8(&bytes[start..*pos]).map_err(|e| e.to_string())?;
        s.parse::<f64>().map(JsonValue::Num).map_err(|e| e.to_string())
    }
}
