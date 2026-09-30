//! Just enough of git's config file syntax to find `core.excludesFile`.

use std::fs;
use std::io;
use std::path::Path;

use crate::error::{Error, Result};

#[derive(Debug, Clone)]
struct Entry {
    section: String,
    subsection: Option<String>,
    key: String,
    value: Option<String>,
}

#[derive(Debug, Default, Clone)]
pub struct GitConfig {
    entries: Vec<Entry>,
}

impl GitConfig {
    /// Reads a config file; a missing file is an empty config.
    pub fn load(path: &Path) -> Result<GitConfig> {
        match fs::read(path) {
            Ok(bytes) => Ok(GitConfig::parse(&String::from_utf8_lossy(&bytes))),
            Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(GitConfig::default()),
            Err(e) => Err(Error::io(path, e)),
        }
    }

    pub fn parse(text: &str) -> GitConfig {
        let mut entries = Vec::new();
        let mut section = String::new();
        let mut subsection: Option<String> = None;
        for line in logical_lines(text) {
            let line = line.trim_start();
            if line.is_empty() || line.starts_with('#') || line.starts_with(';') {
                continue;
            }
            if let Some(header) = line.strip_prefix('[') {
                let Some(end) = header.find(']') else { continue };
                let (name, sub) = parse_header(&header[..end]);
                section = name;
                subsection = sub;
                let tail = header[end + 1..].trim_start();
                if tail.is_empty() || tail.starts_with('#') || tail.starts_with(';') {
                    continue;
                }
                if let Some(entry) = parse_assignment(&section, &subsection, tail) {
                    entries.push(entry);
                }
                continue;
            }
            if let Some(entry) = parse_assignment(&section, &subsection, line) {
                entries.push(entry);
            }
        }
        GitConfig { entries }
    }

    /// Last value set for `section.key` (no subsection).
    pub fn get(&self, section: &str, key: &str) -> Option<&str> {
        self.entries
            .iter()
            .rev()
            .find(|e| e.subsection.is_none() && e.section.eq_ignore_ascii_case(section) && e.key == key)
            .and_then(|e| e.value.as_deref())
    }
}

/// Joins lines ending in a backslash with the following line.
fn logical_lines(text: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut current = String::new();
    for raw in text.split('\n') {
        let raw = raw.strip_suffix('\r').unwrap_or(raw);
        if let Some(head) = raw.strip_suffix('\\') {
            if !head.ends_with('\\') {
                current.push_str(head);
                continue;
            }
        }
        current.push_str(raw);
        out.push(std::mem::take(&mut current));
    }
    if !current.is_empty() {
        out.push(current);
    }
    out
}

fn parse_header(header: &str) -> (String, Option<String>) {
    let header = header.trim();
    if let Some(space) = header.find(char::is_whitespace) {
        let name = header[..space].to_ascii_lowercase();
        let sub = header[space..].trim().trim_matches('"').to_string();
        return (name, Some(sub));
    }
    match header.split_once('.') {
        Some((name, sub)) => (name.to_ascii_lowercase(), Some(sub.to_ascii_lowercase())),
        None => (header.to_ascii_lowercase(), None),
    }
}

fn parse_assignment(section: &str, subsection: &Option<String>, line: &str) -> Option<Entry> {
    let (key, value) = match line.find('=') {
        Some(eq) => (line[..eq].trim(), Some(parse_value(&line[eq + 1..]))),
        None => (strip_comment(line).trim(), None),
    };
    if key.is_empty() || !key.chars().all(|c| c.is_ascii_alphanumeric() || c == '-') {
        return None;
    }
    Some(Entry {
        section: section.to_string(),
        subsection: subsection.clone(),
        key: key.to_string(),
        value,
    })
}

fn strip_comment(text: &str) -> &str {
    match text.find(['#', ';']) {
        Some(at) => &text[..at],
        None => text,
    }
}

/// Unquotes a value: double quotes group, `\"` `\\` `\n` `\t` `\b` are
/// escapes, `#` and `;` outside quotes start a comment, and unquoted
/// surrounding whitespace is dropped.
fn parse_value(raw: &str) -> String {
    let mut out = String::new();
    let mut pending_space = String::new();
    let mut quoted = false;
    let mut chars = raw.trim_start().chars();
    while let Some(c) = chars.next() {
        match c {
            '"' => {
                out.push_str(&std::mem::take(&mut pending_space));
                quoted = !quoted;
            }
            '\\' => {
                out.push_str(&std::mem::take(&mut pending_space));
                match chars.next() {
                    Some('n') => out.push('\n'),
                    Some('t') => out.push('\t'),
                    Some('b') => out.push('\u{8}'),
                    Some(other) => out.push(other),
                    None => {}
                }
            }
            '#' | ';' if !quoted => break,
            c if c.is_whitespace() && !quoted => pending_space.push(c),
            c => {
                out.push_str(&std::mem::take(&mut pending_space));
                out.push(c);
            }
        }
    }
    out
}
