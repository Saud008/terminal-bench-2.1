use std::path::PathBuf;

use crate::error::{Error, Result};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Command {
    Help,
    List,
    Check(Vec<String>),
}

#[derive(Debug, Clone)]
pub struct Options {
    pub root: PathBuf,
    pub command: Command,
}

pub fn parse(argv: &[String]) -> Result<Options> {
    let mut root: Option<PathBuf> = None;
    let mut i = 0;
    while i < argv.len() {
        let arg = argv[i].as_str();
        if arg == "-h" || arg == "--help" {
            return Ok(Options { root: root.unwrap_or_else(|| PathBuf::from(".")), command: Command::Help });
        } else if arg == "--root" {
            let value = argv
                .get(i + 1)
                .ok_or_else(|| Error::Usage("--root needs a directory".to_string()))?;
            root = Some(PathBuf::from(value));
            i += 2;
        } else if let Some(value) = arg.strip_prefix("--root=") {
            root = Some(PathBuf::from(value));
            i += 1;
        } else if arg.starts_with('-') {
            return Err(Error::Usage(format!("unknown option {arg}")));
        } else {
            break;
        }
    }

    let root = root.unwrap_or_else(|| PathBuf::from("."));
    let rest = argv.get(i + 1..).unwrap_or(&[]);
    let command = match argv.get(i).map(String::as_str) {
        None => return Err(Error::Usage("missing command".to_string())),
        Some("list") => {
            if !rest.is_empty() {
                return Err(Error::Usage("list takes no arguments".to_string()));
            }
            Command::List
        }
        Some("check") => {
            let paths = match rest.first().map(String::as_str) {
                Some("--") => &rest[1..],
                _ => rest,
            };
            if paths.is_empty() {
                return Err(Error::Usage("check needs at least one path".to_string()));
            }
            Command::Check(paths.to_vec())
        }
        Some(other) => return Err(Error::Usage(format!("unknown command {other}"))),
    };
    Ok(Options { root, command })
}
