use crate::util::json;

#[derive(Debug, Clone)]
pub struct Stanza {
    pub type_name: String,
    pub args: Vec<String>,
    pub fingerprint: String,
}

impl Stanza {
    pub fn to_json(&self) -> String {
        format!(
            "{{\"type\":\"{}\",\"args\":{},\"fingerprint\":\"{}\"}}",
            json::escape(&self.type_name),
            json::string_array(&self.args),
            json::escape(&self.fingerprint)
        )
    }
}

#[derive(Debug, Clone)]
pub struct ParsedFile {
    pub file_id: String,
    pub rel_path: String,
    pub parse_ok: bool,
    pub stanzas: Vec<Stanza>,
}

impl ParsedFile {
    pub fn to_json(&self) -> String {
        let stanzas: Vec<String> = self.stanzas.iter().map(|s| s.to_json()).collect();
        format!(
            "{{\"file_id\":\"{}\",\"rel_path\":\"{}\",\"parse_ok\":{},\"stanzas\":[{}]}}",
            json::escape(&self.file_id),
            json::escape(&self.rel_path),
            self.parse_ok,
            stanzas.join(",")
        )
    }
}

pub fn parse_age_header(bytes: &[u8], file_id: &str, rel_path: &str) -> ParsedFile {
    let text = String::from_utf8_lossy(bytes);
    let mut lines = text.lines().peekable();
    while let Some(l) = lines.peek() {
        if l.trim().is_empty() {
            lines.next();
            continue;
        }
        break;
    }
    let mut stanzas = Vec::new();
    let mut saw_magic = false;
    let mut parse_ok = true;
    for line in lines {
        let t = line.trim_end();
        if t == "age-encryption.org/v1" {
            saw_magic = true;
            continue;
        }
        if t == "---" {
            break;
        }
        if let Some(rest) = t.strip_prefix("-> ") {
            let mut parts = rest.split_whitespace();
            if let Some(ty) = parts.next() {
                let args: Vec<String> = parts.map(|s| s.to_string()).collect();
                stanzas.push(Stanza {
                    type_name: ty.to_string(),
                    args,
                    fingerprint: String::new(),
                });
            } else {
                parse_ok = false;
            }
        } else if saw_magic {
            continue;
        }
    }
    if !saw_magic && stanzas.is_empty() {
        parse_ok = false;
    }
    ParsedFile {
        file_id: file_id.to_string(),
        rel_path: rel_path.to_string(),
        parse_ok,
        stanzas,
    }
}
