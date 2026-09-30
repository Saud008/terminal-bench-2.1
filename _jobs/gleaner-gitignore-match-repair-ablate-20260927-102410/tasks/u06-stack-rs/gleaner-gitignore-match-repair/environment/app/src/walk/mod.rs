pub mod order;
mod tree;

pub use tree::collect_kept;

use crate::error::{Error, Result};

/// Paths given to `check` must be relative to the root and made only of
/// ordinary components.
pub fn validate_relative(path: &str) -> Result<()> {
    let ok = !path.is_empty()
        && !path.starts_with('/')
        && path.split('/').all(|c| !c.is_empty() && c != "." && c != "..");
    if ok {
        Ok(())
    } else {
        Err(Error::BadPath(path.to_string()))
    }
}
