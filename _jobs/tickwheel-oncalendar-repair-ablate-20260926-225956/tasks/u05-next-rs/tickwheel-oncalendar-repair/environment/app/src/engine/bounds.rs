use super::Clock;
use crate::civil::Tm;
use crate::errno::Errno;
use crate::spec::{BITS_WEEKDAYS, MAX_YEAR};

pub enum Bounds {
    /// Fields were already in range.
    Exact,
    /// Fields were out of range and have been folded forward into `*tm`;
    /// the caller has to restart matching from there.
    Moved,
}

/// Folds out-of-range fields (April 31st, hour 24, a wall time skipped by a
/// clock change, ...) and reports whether that moved the time.
pub fn tm_within_bounds(tm: &mut Tm, clock: &mut Clock) -> Result<Bounds, Errno> {
    if tm.year + 1900 > MAX_YEAR {
        return Err(Errno::Range);
    }

    let mut t = *tm;
    if clock.mktime(&mut t) < 0 {
        return Err(Errno::Overflow);
    }

    use std::cmp::Ordering;
    let cmp = (t.year, t.mon, t.mday, t.hour, t.min, t.sec).cmp(&(tm.year, tm.mon, tm.mday, tm.hour, tm.min, tm.sec));

    match cmp {
        Ordering::Less => Err(Errno::DeadLk),
        Ordering::Greater => {
            *tm = t;
            Ok(Bounds::Moved)
        }
        Ordering::Equal => Ok(Bounds::Exact),
    }
}

pub fn matches_weekday(bits: i32, tm: &Tm, clock: &mut Clock) -> bool {
    if bits < 0 || bits >= BITS_WEEKDAYS {
        return true;
    }

    let mut t = *tm;
    if clock.mktime(&mut t) < 0 {
        return false;
    }

    let k = if t.wday == 0 { 6 } else { t.wday - 1 };
    bits & (1 << k) != 0
}
