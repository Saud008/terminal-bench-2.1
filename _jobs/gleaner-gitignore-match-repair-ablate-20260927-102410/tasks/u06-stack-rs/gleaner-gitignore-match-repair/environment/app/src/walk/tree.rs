use std::fs;

use crate::error::{Error, Result};
use crate::ignore::{Hit, Matcher, PatternList};

/// Entries with this name are never listed or entered, at any depth.
const GIT_DIR: &str = ".git";

/// Every non-ignored file below the root, relative to it, in no particular
/// order.
pub fn collect_kept(matcher: &Matcher) -> Result<Vec<String>> {
    let mut out = Vec::new();
    let mut stack = vec![matcher.dir_list("")?];
    visit(matcher, "", None, &mut stack, &mut out)?;
    Ok(out)
}

fn visit(
    matcher: &Matcher,
    dir: &str,
    inherited: Option<Hit>,
    stack: &mut Vec<PatternList>,
    out: &mut Vec<String>,
) -> Result<()> {
    let abs = matcher.root().join(dir);
    let entries = fs::read_dir(&abs).map_err(|e| Error::io(&abs, e))?;
    for entry in entries {
        let entry = entry.map_err(|e| Error::io(&abs, e))?;
        let name = entry
            .file_name()
            .into_string()
            .map_err(|_| Error::NotUtf8(entry.path()))?;
        if name == GIT_DIR {
            continue;
        }
        let rel = if dir.is_empty() { name } else { format!("{dir}/{name}") };
        let is_dir = entry.file_type().map_err(|e| Error::io(&entry.path(), e))?.is_dir();
        let own = matcher.classify(stack, &rel, is_dir);
        let resolved = crate::ignore::resolve(inherited.clone(), own);
        let ignored = matches!(&resolved, Some(h) if !h.negative);
        if is_dir {
            stack.push(matcher.dir_list(&rel)?);
            let result = visit(matcher, &rel, crate::ignore::inherit(&resolved), stack, out);
            stack.pop();
            result?;
        } else if !ignored {
            out.push(rel);
        }
    }
    Ok(())
}
