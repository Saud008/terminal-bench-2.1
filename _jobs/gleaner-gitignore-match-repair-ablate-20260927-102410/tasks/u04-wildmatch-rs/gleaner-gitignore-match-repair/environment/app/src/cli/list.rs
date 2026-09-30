use std::io::Write;

use crate::cli::Options;
use crate::error::{Error, Result};
use crate::ignore::Matcher;
use crate::report;
use crate::walk;

pub fn run(opts: &Options) -> Result<u8> {
    let matcher = Matcher::open(&opts.root)?;
    let kept = walk::collect_kept(&matcher)?;
    let out = report::list_lines(&walk::order::sort_paths(kept));
    std::io::stdout()
        .write_all(out.as_bytes())
        .map_err(|e| Error::io("<stdout>".as_ref(), e))?;
    Ok(0)
}
