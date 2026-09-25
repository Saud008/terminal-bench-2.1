use crate::checksum;
use crate::model::ParsedSentence;

pub fn parse_line(line: &str) -> Result<ParsedSentence, String> {
    let line = line.trim();
    if !line.starts_with('$') || !checksum::verify_checksum(line) {
        return Err("checksum".into());
    }
    let star = line.rfind('*').unwrap();
    let body = &line[1..star];
    let mut parts = split_fields(body);
    if parts.is_empty() {
        return Err("empty".into());
    }
    let addr = parts.remove(0);
    if addr.len() < 5 {
        return Err("addr".into());
    }
    let talker = addr[..2].to_string();
    let sentence = addr[2..].to_string();
    let is_multipart = matches!(sentence.as_str(), "GSV" | "GSA")
        && parts.len() >= 2
        && parts[0].parse::<u32>().ok().filter(|&t| t > 1).is_some();
    Ok(ParsedSentence {
        raw: line.to_string(),
        talker,
        sentence,
        fields: parts,
        is_multipart,
    })
}

fn split_fields(body: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut in_quotes = false;
    let chars: Vec<char> = body.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        let c = chars[i];
        if in_quotes {
            if c == '"' {
                if i + 1 < chars.len() && chars[i + 1] == '"' {
                    cur.push('"');
                    i += 2;
                    continue;
                }
                in_quotes = false;
                cur.push('"'); // preserve closing quote in field value? Contract: surrounding quotes preserved
                // Actually: surrounding quotes are preserved — open quote was pushed when entering.
                i += 1;
                continue;
            }
            cur.push(c);
            i += 1;
            continue;
        }
        if c == '"' {
            in_quotes = true;
            cur.push('"'); // preserve opening quote
            i += 1;
            continue;
        }
        if c == ',' {
            out.push(cur);
            cur = String::new();
            i += 1;
            continue;
        }
        cur.push(c);
        i += 1;
    }
    out.push(cur);
    out
}
