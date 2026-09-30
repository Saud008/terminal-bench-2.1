use std::io::Write;

use crate::cli::Options;
use crate::error::{Error, Result};
use crate::ignore::Matcher;
use crate::report;
use crate::walk;

pub fn run(opts: &Options, paths: &[String]) -> Result<u8> {
    for path in paths {
        walk::validate_relative(path)?;
    }
    let matcher = Matcher::open(&opts.root)?;
    let mut out = String::new();
    let mut any_ignored = false;
    for path in paths {
        let verdict = matcher.check_path(path)?;
        any_ignored |= verdict.is_ignored();
        out.push_str(&report::check_line(path, &verdict));
    }
    std::io::stdout()
        .write_all(out.as_bytes())
        .map_err(|e| Error::io("<stdout>".as_ref(), e))?;
    Ok(if any_ignored { 0 } else { 1 })
}
