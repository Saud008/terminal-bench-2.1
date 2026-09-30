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
