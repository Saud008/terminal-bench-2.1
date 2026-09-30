//! Calendar event expressions (`OnCalendar=` syntax).

mod format;
mod normalize;
mod parse;

pub use parse::parse;

pub const BITS_WEEKDAYS: i32 = 127;
pub const MIN_YEAR: i32 = 1970;
pub const MAX_YEAR: i32 = 2199;
pub const COMPONENTS_MAX: usize = 240;

/// One element of a comma separated list: `start`, `start..stop`,
/// `start/repeat` or `start..stop/repeat`. `stop` is -1 when absent and
/// `repeat` is 0 when absent.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Component {
    pub start: i32,
    pub stop: i32,
    pub repeat: i32,
}

impl Component {
    pub fn single(v: i32) -> Component {
        Component { start: v, stop: -1, repeat: 0 }
    }
}

/// A field list. `None` stands for `*` (every value); the seconds field
/// stores `*` explicitly as `0/1s` instead, see parse.rs.
pub type Chain = Option<Vec<Component>>;

#[derive(Debug, Clone, Default)]
pub struct CalendarSpec {
    /// Bit 0 is Monday. 0 or -1 mean "any weekday".
    pub weekdays_bits: i32,
    pub end_of_month: bool,
    pub utc: bool,
    pub timezone: Option<String>,

    pub year: Chain,
    pub month: Chain,
    pub day: Chain,
    pub hour: Chain,
    pub minute: Chain,
    /// Seconds, in microseconds.
    pub microsecond: Chain,
}

impl CalendarSpec {
    pub fn to_normalized_string(&self) -> String {
        format::to_string(self)
    }
}
