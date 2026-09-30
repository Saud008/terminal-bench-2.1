use std::fmt;

/// A transcript line crumbjar could not understand.
#[derive(Debug)]
pub struct LineError {
    pub line: usize,
    pub msg: String,
}

impl fmt::Display for LineError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "line {}: {}", self.line, self.msg)
    }
}
