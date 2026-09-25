use std::collections::HashMap;

use crate::error::{FcError, Result};
use crate::model::{CharsetEntry, FontConfig};

pub fn find_cycle(_cfg: &FontConfig) -> Result<()> {
    Ok(())
}

pub fn lookup_charset<'a>(cfg: &'a FontConfig, name: &str) -> Result<&'a CharsetEntry> {
    let basename = name.split(':').next().unwrap_or(name);
    cfg.charsets
        .iter()
        .find(|c| c.name == basename || c.short == name || c.short == basename)
        .ok_or_else(|| FcError::UnknownCharset(name.to_string()))
}

pub fn expand_alias_chain(cfg: &FontConfig, start: &str) -> Result<(Vec<String>, String)> {
    let edges: HashMap<&str, &str> = cfg
        .aliases
        .iter()
        .map(|(a, b)| (a.as_str(), b.as_str()))
        .collect();

    if lookup_charset(cfg, start).is_ok() {
        return Ok((Vec::new(), start.to_string()));
    }

    match edges.get(start) {
        Some(next) => {
            if lookup_charset(cfg, next).is_ok() {
                Ok((vec![start.to_string()], (*next).to_string()))
            } else {
                Ok((vec![start.to_string()], (*next).to_string()))
            }
        }
        None => Err(FcError::UnknownAlias(start.to_string())),
    }
}
