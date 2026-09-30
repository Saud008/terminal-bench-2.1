use std::fmt;

/// The error kinds tickwheel reports. The messages are the strerror(3)
/// texts of the corresponding errno values so diagnostics read the same as
/// the rest of the platform tooling.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Errno {
    Inval,
    Range,
    NoBufs,
    NoEnt,
    DeadLk,
    Overflow,
}

impl Errno {
    pub fn message(self) -> &'static str {
        match self {
            Errno::Inval => "Invalid argument",
            Errno::Range => "Numerical result out of range",
            Errno::NoBufs => "No buffer space available",
            Errno::NoEnt => "No such file or directory",
            Errno::DeadLk => "Resource deadlock avoided",
            Errno::Overflow => "Value too large for defined data type",
        }
    }
}

impl fmt::Display for Errno {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.message())
    }
}
