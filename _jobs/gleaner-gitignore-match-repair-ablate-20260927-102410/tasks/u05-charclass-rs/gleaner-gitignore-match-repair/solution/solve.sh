#!/usr/bin/env bash
set -euo pipefail

cd /app

# Skip a leading byte order mark, drop the CR of CRLF line ends, and number lines as they are in the file.
cat > /app/src/ignore/lines.rs <<'RUST'
//! Splitting a pattern file into candidate lines.

const UTF8_BOM: &[u8] = b"\xef\xbb\xbf";

/// A line that may hold a pattern, with its 1-based line number in the file.
#[derive(Debug, Clone)]
pub struct RawLine {
    pub number: usize,
    pub text: Vec<u8>,
}

/// Splits file contents on `\n`, dropping blank lines and `#` comments.
/// A UTF-8 byte order mark at the start of the file is skipped and a `\r`
/// before the newline is not part of the line.
pub fn split(buf: &[u8]) -> Vec<RawLine> {
    let body = buf.strip_prefix(UTF8_BOM).unwrap_or(buf);
    let mut out = Vec::new();
    for (index, line) in body.split(|&b| b == b'\n').enumerate() {
        if line.is_empty() || line[0] == b'#' {
            continue;
        }
        let line = line.strip_suffix(b"\r").unwrap_or(line);
        out.push(RawLine { number: index + 1, text: line.to_vec() });
    }
    out
}
RUST

# Trim only unescaped trailing spaces, leave a leading backslash to the matcher, and strip the trailing slash before deciding whether the pattern has a slash.
cat > /app/src/ignore/parse.rs <<'RUST'
//! Turning one line of a pattern file into a pattern.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Parsed {
    /// The line as it is reported by `check`: trailing spaces removed,
    /// everything else as written.
    pub text: Vec<u8>,
    /// What is matched: `text` without a leading `!` or a trailing `/`.
    pub body: Vec<u8>,
    pub negative: bool,
    pub dir_only: bool,
    /// No `/` left in `body`: the pattern is matched against the last path
    /// component at any depth.
    pub basename_only: bool,
}

/// Removes unescaped trailing spaces. Only the space character counts, and
/// a space preceded by a backslash is kept.
pub fn trim_trailing_spaces(line: &[u8]) -> &[u8] {
    let mut last_space: Option<usize> = None;
    let mut i = 0;
    while i < line.len() {
        match line[i] {
            b' ' => {
                if last_space.is_none() {
                    last_space = Some(i);
                }
            }
            b'\\' => {
                i += 1;
                if i >= line.len() {
                    return line;
                }
                last_space = None;
            }
            _ => last_space = None,
        }
        i += 1;
    }
    match last_space {
        Some(at) => &line[..at],
        None => line,
    }
}

pub fn parse_line(line: &[u8]) -> Option<Parsed> {
    let text = trim_trailing_spaces(line);
    if text.is_empty() {
        return None;
    }
    let mut body = text;
    let negative = body[0] == b'!';
    if negative {
        body = &body[1..];
    }
    let dir_only = body.last() == Some(&b'/');
    if dir_only {
        body = &body[..body.len() - 1];
    }
    let basename_only = !body.contains(&b'/');
    Some(Parsed {
        text: text.to_vec(),
        body: body.to_vec(),
        negative,
        dir_only,
        basename_only,
    })
}
RUST

# Slash patterns are relative to the directory of the .gitignore they come from.
cat > /app/src/ignore/pattern.rs <<'RUST'
use super::lines;
use super::parse::parse_line;
use super::wildmatch::wildmatch;

#[derive(Debug, Clone)]
pub struct Pattern {
    pub text: String,
    pub body: Vec<u8>,
    pub negative: bool,
    pub dir_only: bool,
    pub basename_only: bool,
    pub line: usize,
}

/// The patterns of one file, with the directory they are relative to.
#[derive(Debug, Clone, Default)]
pub struct PatternList {
    /// How the file is named in `check` output.
    pub source: String,
    /// Directory of a `.gitignore`, relative to the root and without a
    /// trailing slash; empty for the root and for non-directory sources.
    pub base: String,
    pub patterns: Vec<Pattern>,
}

impl PatternList {
    pub fn empty(source: &str, base: &str) -> PatternList {
        PatternList { source: source.to_string(), base: base.to_string(), patterns: Vec::new() }
    }

    pub fn from_bytes(source: &str, base: &str, buf: &[u8]) -> PatternList {
        let mut list = PatternList::empty(source, base);
        for raw in lines::split(buf) {
            if let Some(p) = parse_line(&raw.text) {
                list.patterns.push(Pattern {
                    text: String::from_utf8_lossy(&p.text).into_owned(),
                    body: p.body,
                    negative: p.negative,
                    dir_only: p.dir_only,
                    basename_only: p.basename_only,
                    line: raw.number,
                });
            }
        }
        list
    }

    /// The last pattern in the file that matches `path` (relative to the
    /// root). `basename` is the last component of `path`.
    pub fn last_match(&self, path: &str, basename: &str, is_dir: bool) -> Option<&Pattern> {
        self.patterns.iter().rev().find(|pat| {
            if pat.dir_only && !is_dir {
                return false;
            }
            if pat.basename_only {
                wildmatch(&pat.body, basename.as_bytes(), false)
            } else {
                match_pathname(path, &self.base, &pat.body)
            }
        })
    }
}

/// Patterns containing a slash are matched against the path relative to
/// the directory of the file they come from; a leading `/` only marks that.
fn match_pathname(path: &str, base: &str, body: &[u8]) -> bool {
    let body = body.strip_prefix(b"/").unwrap_or(body);
    let rest = if base.is_empty() {
        path
    } else {
        match path.strip_prefix(base).and_then(|r| r.strip_prefix('/')) {
            Some(r) => r,
            None => return false,
        }
    };
    wildmatch(body, rest.as_bytes(), true)
}
RUST

# A run of stars only crosses directories when it is a whole component, and `**/` may also match no directory.
cat > /app/src/ignore/wildmatch.rs <<'RUST'
//! Glob matching with git's wildmatch rules.
//!
//! With `pathname` set, `*`, `?` and bracket expressions never match `/`,
//! and `**` is special when it forms a whole path component. Without it
//! every `*` may match `/` (only used for single components).

use super::charclass;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Outcome {
    Match,
    NoMatch,
    AbortAll,
    AbortToStarStar,
}

pub fn wildmatch(pattern: &[u8], text: &[u8], pathname: bool) -> bool {
    dowild(pattern, 0, text, 0, pathname) == Outcome::Match
}

fn is_glob_special(c: u8) -> bool {
    matches!(c, b'*' | b'?' | b'[' | b'\\')
}

fn dowild(pat: &[u8], mut p: usize, text: &[u8], mut t: usize, pathname: bool) -> Outcome {
    let start = p;
    while p < pat.len() {
        let p_ch = pat[p];
        let t_ch = text.get(t).copied();
        if t_ch.is_none() && p_ch != b'*' {
            return Outcome::AbortAll;
        }
        match p_ch {
            b'\\' => {
                p += 1;
                if pat.get(p).copied() != t_ch {
                    return Outcome::NoMatch;
                }
            }
            b'?' => {
                if pathname && t_ch == Some(b'/') {
                    return Outcome::NoMatch;
                }
            }
            b'*' => return star(pat, p, start, text, t, pathname),
            b'[' => {
                let tc = t_ch.unwrap_or(0);
                match charclass::bracket(pat, p + 1, tc) {
                    None => return Outcome::AbortAll,
                    Some((hit, end)) => {
                        if !hit || (pathname && tc == b'/') {
                            return Outcome::NoMatch;
                        }
                        p = end;
                    }
                }
            }
            _ => {
                if t_ch != Some(p_ch) {
                    return Outcome::NoMatch;
                }
            }
        }
        p += 1;
        t += 1;
    }
    if t < text.len() {
        Outcome::NoMatch
    } else {
        Outcome::Match
    }
}

/// Handles a run of `*` starting at `pat[p]`; `start` is where the current
/// (sub)pattern began.
fn star(pat: &[u8], mut p: usize, start: usize, text: &[u8], mut t: usize, pathname: bool) -> Outcome {
    let match_slash;
    p += 1;
    if pat.get(p) == Some(&b'*') {
        let before = if p >= start + 2 { Some(pat[p - 2]) } else { None };
        while pat.get(p) == Some(&b'*') {
            p += 1;
        }
        let after = pat.get(p).copied();
        if !pathname {
            match_slash = true;
        } else if (before.is_none() || before == Some(b'/'))
            && (after.is_none()
                || after == Some(b'/')
                || (after == Some(b'\\') && pat.get(p + 1) == Some(&b'/')))
        {
            // `**/` may also match no directory at all.
            if after == Some(b'/') && dowild(pat, p + 1, text, t, pathname) == Outcome::Match {
                return Outcome::Match;
            }
            match_slash = true;
        } else {
            match_slash = false;
        }
    } else {
        match_slash = !pathname;
    }

    if p == pat.len() {
        if !match_slash && text[t..].contains(&b'/') {
            return Outcome::NoMatch;
        }
        return Outcome::Match;
    }
    if !match_slash && pat[p] == b'/' {
        // A single `*` followed by `/` swallows the rest of this component.
        let Some(off) = text[t..].iter().position(|&c| c == b'/') else {
            return Outcome::NoMatch;
        };
        t += off;
        return dowild(pat, p + 1, text, t + 1, pathname);
    }

    let mut t_ch = text.get(t).copied();
    while t_ch.is_some() {
        if !is_glob_special(pat[p]) {
            let lit = pat[p];
            while let Some(c) = text.get(t).copied() {
                if (!match_slash && c == b'/') || c == lit {
                    break;
                }
                t += 1;
            }
            t_ch = text.get(t).copied();
            if t_ch != Some(lit) {
                return if match_slash { Outcome::AbortAll } else { Outcome::AbortToStarStar };
            }
        }
        let matched = dowild(pat, p, text, t, pathname);
        if matched != Outcome::NoMatch {
            if !match_slash || matched != Outcome::AbortToStarStar {
                return matched;
            }
        } else if !match_slash && t_ch == Some(b'/') {
            return Outcome::AbortToStarStar;
        }
        t += 1;
        t_ch = text.get(t).copied();
    }
    Outcome::AbortAll
}
RUST

# `[^...]` negates like `[!...]`, and a `]` right after the opening bracket is a member.

# Deeper .gitignore files win, and a negation can't rescue anything inside an excluded directory.
cat > /app/src/ignore/stack.rs <<'RUST'
//! Combining all pattern sources into a decision for one path.

use std::path::{Path, PathBuf};

use super::pattern::{Pattern, PatternList};
use super::sources::{read_optional, Sources};
use crate::error::Result;

pub const PER_DIRECTORY: &str = ".gitignore";

/// The pattern that decided a path.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Hit {
    pub source: String,
    pub line: usize,
    pub text: String,
    pub negative: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Verdict {
    NoMatch,
    Matched(Hit),
}

impl Verdict {
    pub fn is_ignored(&self) -> bool {
        matches!(self, Verdict::Matched(hit) if !hit.negative)
    }
}

pub struct Matcher {
    root: PathBuf,
    /// `.git/info/exclude` and the excludes file, highest precedence first.
    globals: Vec<PatternList>,
}

fn hit(list: &PatternList, pat: &Pattern) -> Hit {
    Hit { source: list.source.clone(), line: pat.line, text: pat.text.clone(), negative: pat.negative }
}

/// Combines the decision inherited from an excluded parent directory with
/// the path's own last matching pattern. Once a directory is excluded
/// nothing below it can be re-included.
pub fn resolve(inherited: Option<Hit>, own: Option<Hit>) -> Option<Hit> {
    inherited.or(own)
}

/// What an excluded directory passes on to its entries.
pub fn inherit(resolved: &Option<Hit>) -> Option<Hit> {
    match resolved {
        Some(h) if !h.negative => Some(h.clone()),
        _ => None,
    }
}

impl Matcher {
    pub fn open(root: &Path) -> Result<Matcher> {
        let sources = Sources::discover(root)?;
        let globals = sources.load(root)?;
        Ok(Matcher { root: root.to_path_buf(), globals })
    }

    pub fn root(&self) -> &Path {
        &self.root
    }

    /// The `.gitignore` of `dir` (relative to the root, "" for the root).
    pub fn dir_list(&self, dir: &str) -> Result<PatternList> {
        let (file, source) = if dir.is_empty() {
            (self.root.join(PER_DIRECTORY), PER_DIRECTORY.to_string())
        } else {
            (self.root.join(dir).join(PER_DIRECTORY), format!("{dir}/{PER_DIRECTORY}"))
        };
        Ok(match read_optional(&file, &source)? {
            Some(mut list) => {
                list.base = dir.to_string();
                list
            }
            None => PatternList::empty(&source, dir),
        })
    }

    /// Last matching pattern for `path`, given the `.gitignore` lists of its
    /// ancestors from the root down (`stack`). Deeper files override
    /// shallower ones; all of them override the tree-wide sources.
    pub fn classify(&self, stack: &[PatternList], path: &str, is_dir: bool) -> Option<Hit> {
        let basename = path.rsplit('/').next().unwrap_or(path);
        stack
            .iter()
            .rev()
            .chain(self.globals.iter())
            .find_map(|list| list.last_match(path, basename, is_dir).map(|p| hit(list, p)))
    }

    /// Decision for a single path relative to the root.
    pub fn check_path(&self, path: &str) -> Result<Verdict> {
        let mut stack = vec![self.dir_list("")?];
        let mut inherited: Option<Hit> = None;
        let components: Vec<&str> = path.split('/').collect();
        let mut prefix = String::new();
        for comp in &components[..components.len() - 1] {
            if !prefix.is_empty() {
                prefix.push('/');
            }
            prefix.push_str(comp);
            let own = self.classify(&stack, &prefix, true);
            inherited = inherit(&resolve(inherited, own));
            stack.push(self.dir_list(&prefix)?);
        }
        let is_dir = self
            .root
            .join(path)
            .symlink_metadata()
            .map(|m| m.is_dir())
            .unwrap_or(false);
        let own = self.classify(&stack, path, is_dir);
        Ok(match resolve(inherited, own) {
            Some(h) => Verdict::Matched(h),
            None => Verdict::NoMatch,
        })
    }
}
RUST

# .git/info/exclude outranks the excludes file.
cat > /app/src/ignore/sources.rs <<'RUST'
//! The pattern files that apply to the whole tree.

use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use super::pattern::PatternList;
use crate::config::{paths, GitConfig};
use crate::error::{Error, Result};

pub const INFO_EXCLUDE: &str = ".git/info/exclude";

#[derive(Debug, Clone)]
pub struct Sources {
    /// `core.excludesFile` as configured (after `~/` expansion), or the
    /// default location when it is not set.
    pub excludes_file: Option<String>,
}

impl Sources {
    pub fn discover(root: &Path) -> Result<Sources> {
        let config = GitConfig::load(&root.join(".git").join("config"))?;
        let excludes_file = match config.get("core", "excludesFile") {
            Some(value) => paths::expand_user(value),
            None => paths::default_excludes_file(),
        };
        Ok(Sources { excludes_file })
    }

    /// Loads the tree-wide lists, highest precedence first.
    pub fn load(&self, root: &Path) -> Result<Vec<PatternList>> {
        let mut lists = Vec::new();
        if let Some(list) = read_optional(&root.join(INFO_EXCLUDE), INFO_EXCLUDE)? {
            lists.push(list);
        }
        if let Some(name) = &self.excludes_file {
            let path = resolve(root, name);
            if let Some(list) = read_optional(&path, name)? {
                lists.push(list);
            }
        }
        Ok(lists)
    }
}

/// Relative excludes-file paths are taken from the root.
fn resolve(root: &Path, name: &str) -> PathBuf {
    let path = Path::new(name);
    if path.is_absolute() {
        path.to_path_buf()
    } else {
        root.join(path)
    }
}

/// Reads a pattern file; a missing file (or a directory) gives `None`.
pub fn read_optional(path: &Path, source: &str) -> Result<Option<PatternList>> {
    match fs::read(path) {
        Ok(buf) => Ok(Some(PatternList::from_bytes(source, "", &buf))),
        Err(e)
            if matches!(
                e.kind(),
                io::ErrorKind::NotFound | io::ErrorKind::IsADirectory | io::ErrorKind::NotADirectory
            ) =>
        {
            Ok(None)
        }
        Err(e) => Err(Error::io(path, e)),
    }
}
RUST

# The default excludes file lives under XDG_CONFIG_HOME when that is set and not empty.
cat > /app/src/config/paths.rs <<'RUST'
use std::env;

fn home() -> Option<String> {
    env::var("HOME").ok()
}

/// Expands a leading `~/` (or a lone `~`) to `$HOME`. Other values are
/// returned unchanged.
pub fn expand_user(value: &str) -> Option<String> {
    if value == "~" {
        return home();
    }
    match value.strip_prefix("~/") {
        Some(rest) => home().map(|h| format!("{h}/{rest}")),
        None => Some(value.to_string()),
    }
}

/// The excludes file git reads when `core.excludesFile` is not set.
pub fn default_excludes_file() -> Option<String> {
    match env::var("XDG_CONFIG_HOME") {
        Ok(dir) if !dir.is_empty() => Some(format!("{dir}/git/ignore")),
        _ => home().map(|h| format!("{h}/.config/git/ignore")),
    }
}
RUST

# Config key names are case-insensitive.
cat > /app/src/config/gitconfig.rs <<'RUST'
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

    /// Last value set for `section.key` (no subsection). Section and key
    /// names are case-insensitive, as in git.
    pub fn get(&self, section: &str, key: &str) -> Option<&str> {
        self.entries
            .iter()
            .rev()
            .find(|e| {
                e.subsection.is_none()
                    && e.section.eq_ignore_ascii_case(section)
                    && e.key.eq_ignore_ascii_case(key)
            })
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
RUST

# git ls-files order is plain byte order of the whole path.
cat > /app/src/walk/order.rs <<'RUST'
/// Sorts listed paths the way `git ls-files` prints them: by the bytes of
/// the whole relative path, so `a-b` comes before `a/b` and `a/b` before
/// `a0`.
pub fn sort_paths(mut paths: Vec<String>) -> Vec<String> {
    paths.sort_unstable();
    paths
}
RUST

cargo build --release --offline
