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
                match_pathname(path, &pat.body)
            }
        })
    }
}

/// Patterns containing a slash are matched against the whole path.
fn match_pathname(path: &str, body: &[u8]) -> bool {
    let body = body.strip_prefix(b"/").unwrap_or(body);
    wildmatch(body, path.as_bytes(), true)
}
