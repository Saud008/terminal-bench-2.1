//! Next-elapse computation.

mod bounds;
mod matching;
mod next;

use crate::civil::{mktime::mktime, Tm, USEC_PER_SEC};
use crate::errno::Errno;
use crate::spec::CalendarSpec;
use crate::zone::Zone;

/// Largest timestamp (µs) the formatter can print; later base times are
/// rejected.
pub const USEC_TIMESTAMP_FORMATTABLE_MAX: u64 = 253_402_214_399_999_999;

/// Wall clock used while evaluating one expression.
pub struct Clock {
    zone: Zone,
    offset: i64,
}

impl Clock {
    fn for_spec(spec: &CalendarSpec) -> Result<Clock, Errno> {
        let zone = match (&spec.timezone, spec.utc) {
            (Some(name), false) => Zone::load(name).ok_or(Errno::Inval)?,
            _ => Zone::Utc,
        };
        Ok(Clock { zone, offset: 0 })
    }

    pub fn localtime(&self, t: i64) -> Tm {
        self.zone.localtime(t)
    }

    pub fn mktime(&mut self, tm: &mut Tm) -> i64 {
        let mut hint = self.offset;
        mktime(tm, &self.zone, &mut hint)
    }
}

/// First elapse strictly after `usec` (µs since the epoch).
pub fn next_usec(spec: &CalendarSpec, usec: u64) -> Result<u64, Errno> {
    if usec > USEC_TIMESTAMP_FORMATTABLE_MAX {
        return Err(Errno::Inval);
    }

    let mut clock = Clock::for_spec(spec)?;

    let usec = usec + 1;
    let t = (usec / USEC_PER_SEC as u64) as i64;
    let mut tm = clock.localtime(t);
    let mut tm_usec = (usec % USEC_PER_SEC as u64) as i32;

    next::find_next(spec, &mut clock, &mut tm, &mut tm_usec)?;

    let t = clock.mktime(&mut tm);
    if t < 0 {
        return Err(Errno::Inval);
    }
    Ok(t as u64 * USEC_PER_SEC as u64 + tm_usec as u64)
}
