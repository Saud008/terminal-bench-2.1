use std::collections::{HashMap, HashSet};

use crate::error::{FcError, Result};
use crate::model::{CharsetEntry, FontConfig};

pub fn find_cycle(cfg: &FontConfig) -> Result<()> {
    let edges: HashMap<&str, &str> = cfg
        .aliases
        .iter()
        .map(|(a, b)| (a.as_str(), b.as_str()))
        .collect();

    for (start, _) in &cfg.aliases {
        let mut seen = HashSet::new();
        let mut current = start.as_str();
        loop {
            if !seen.insert(current) {
                return Err(FcError::CycleDetected);
            }
            match edges.get(current) {
                Some(next) => current = next,
                None => break,
            }
        }
    }
    Ok(())
}

pub fn lookup_charset<'a>(cfg: &'a FontConfig, name: &str) -> Result<&'a CharsetEntry> {
    cfg.charsets
        .iter()
        .find(|c| c.name == name)
        .ok_or_else(|| FcError::UnknownCharset(name.to_string()))
}

pub fn expand_alias_chain(cfg: &FontConfig, start: &str) -> Result<(Vec<String>, String)> {
    let edges: HashMap<&str, &str> = cfg
        .aliases
        .iter()
        .map(|(a, b)| (a.as_str(), b.as_str()))
        .collect();

    let mut chain = Vec::new();
    let mut seen = HashSet::new();
    let mut current = start.to_string();

    loop {
        if !seen.insert(current.clone()) {
            return Err(FcError::CycleDetected);
        }
        if lookup_charset(cfg, &current).is_ok() {
            return Ok((chain, current));
        }
        match edges.get(current.as_str()) {
            Some(next) => {
                chain.push(current);
                current = (*next).to_string();
            }
            None => return Err(FcError::UnknownAlias(current)),
        }
    }
}
