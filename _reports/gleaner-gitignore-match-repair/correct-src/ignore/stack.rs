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
