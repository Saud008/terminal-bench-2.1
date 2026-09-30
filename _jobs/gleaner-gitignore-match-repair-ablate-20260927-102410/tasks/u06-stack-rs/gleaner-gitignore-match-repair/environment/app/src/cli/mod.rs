mod args;
mod check;
mod list;

pub use args::{Command, Options};

use crate::error::Result;

pub const USAGE: &str = "\
usage: gleaner [--root DIR] list
       gleaner [--root DIR] check [--] PATH...
";

/// Runs one command line and returns the process exit status.
pub fn run(argv: &[String]) -> Result<u8> {
    let opts = args::parse(argv)?;
    match &opts.command {
        Command::Help => {
            print!("{USAGE}");
            Ok(0)
        }
        Command::List => list::run(&opts),
        Command::Check(paths) => check::run(&opts, paths),
    }
}
