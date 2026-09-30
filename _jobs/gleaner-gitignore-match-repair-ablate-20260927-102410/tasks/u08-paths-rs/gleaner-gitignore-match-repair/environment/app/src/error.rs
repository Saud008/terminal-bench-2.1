use std::fmt;
use std::io;
use std::path::{Path, PathBuf};

#[derive(Debug)]
pub enum Error {
    Usage(String),
    BadPath(String),
    Io { path: PathBuf, source: io::Error },
    NotUtf8(PathBuf),
}

impl Error {
    pub fn io(path: &Path, source: io::Error) -> Error {
        Error::Io { path: path.to_path_buf(), source }
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Usage(msg) => write!(f, "{msg} (try --help)"),
            Error::BadPath(path) => write!(f, "not a plain relative path: '{path}'"),
            Error::Io { path, source } => write!(f, "{}: {source}", path.display()),
            Error::NotUtf8(path) => write!(f, "{}: file name is not valid UTF-8", path.display()),
        }
    }
}

impl std::error::Error for Error {}

pub type Result<T> = std::result::Result<T, Error>;
