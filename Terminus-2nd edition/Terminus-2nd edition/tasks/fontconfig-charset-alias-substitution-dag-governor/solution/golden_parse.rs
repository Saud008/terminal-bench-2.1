use std::fs;
use std::path::Path;

use crate::error::{FcError, Result};
use crate::model::{CharsetEntry, FontConfig, SubstituteBlock};

pub fn parse_config(path: &Path) -> Result<FontConfig> {
    let text = fs::read_to_string(path).map_err(|e| FcError::Io(e.to_string()))?;
    parse_str(&text)
}

pub fn parse_str(text: &str) -> Result<FontConfig> {
    let mut cfg = FontConfig::default();
    let lines: Vec<&str> = text
        .lines()
        .map(str::trim)
        .filter(|l| !l.is_empty() && !l.starts_with("<?") && !l.starts_with("<!"))
        .collect();

    let mut i = 0;
    while i < lines.len() {
        let line = lines[i];
        if let Some(rest) = line.strip_prefix("<alias ") {
            let from = attr_value(rest, "from")?;
            let to = attr_value(rest, "to")?;
            cfg.aliases.push((from, to));
            i += 1;
            continue;
        }
        if let Some(rest) = line.strip_prefix("<charset ") {
            let name = attr_value(rest, "name")?;
            let short = attr_value(rest, "short")?;
            let encoding = attr_value(rest, "encoding")?;
            i += 1;
            let alias_ref = if i < lines.len() && lines[i].contains("<alias ref=") {
                let aref = attr_value(lines[i], "ref")?;
                i += 1;
                if i < lines.len() && lines[i].starts_with("</charset>") {
                    i += 1;
                }
                aref
            } else {
                name.clone()
            };
            cfg.charsets.push(CharsetEntry {
                name,
                short,
                encoding,
                alias_ref,
            });
            continue;
        }
        if let Some(rest) = line.strip_prefix("<substitute ") {
            let family = attr_value(rest, "family")?;
            i += 1;
            let mut preferred = Vec::new();
            while i < lines.len() && lines[i].starts_with("<prefer>") {
                let val = lines[i]
                    .trim_start_matches("<prefer>")
                    .trim_end_matches("</prefer>")
                    .trim()
                    .to_string();
                preferred.push(val);
                i += 1;
            }
            if i < lines.len() && lines[i].starts_with("</substitute>") {
                i += 1;
            }
            cfg.substitutes.push(SubstituteBlock { family, preferred });
            continue;
        }
        if line.starts_with("<reject-bitmap") {
            cfg.reject_bitmap = true;
            i += 1;
            continue;
        }
        if line.starts_with("<reject-outline") {
            cfg.reject_outline = true;
            i += 1;
            continue;
        }
        if line == "<fontconfig>" || line == "</fontconfig>" {
            i += 1;
            continue;
        }
        return Err(FcError::Parse(format!("unexpected line: {line}")));
    }

    Ok(cfg)
}

fn attr_value(line: &str, key: &str) -> Result<String> {
    let needle = format!("{key}=\"");
    let start = line
        .find(&needle)
        .ok_or_else(|| FcError::Parse(format!("missing {key} in {line}")))?
        + needle.len();
    let end = line[start..]
        .find('"')
        .ok_or_else(|| FcError::Parse(format!("unterminated {key} in {line}")))?
        + start;
    Ok(line[start..end].to_string())
}

pub fn load_merged(base: &Path, inject: Option<&Path>) -> Result<FontConfig> {
    let mut cfg = parse_config(base)?;
    if let Some(path) = inject {
        cfg.merge(parse_config(path)?);
    }
    Ok(cfg)
}
