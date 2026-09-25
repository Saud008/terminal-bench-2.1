use std::fmt;

#[derive(Debug)]
pub enum JitterError {
    Io(String),
    Parse(String),
    InvalidStaging,
    MissingInput,
}

impl fmt::Display for JitterError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(m) => write!(f, "io: {m}"),
            Self::Parse(m) => write!(f, "parse: {m}"),
            Self::InvalidStaging => write!(f, "invalid staging"),
            Self::MissingInput => write!(f, "missing input"),
        }
    }
}

impl std::error::Error for JitterError {}
