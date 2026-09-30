use super::bounds::{matches_weekday, tm_within_bounds, Bounds};
use super::matching::{find_matching_component, Match};
use super::Clock;
use crate::civil::{Tm, USEC_PER_SEC};
use crate::errno::Errno;
use crate::spec::CalendarSpec;

/// Safety valve against expressions the search cannot make progress on.
const MAX_CALENDAR_ITERATIONS: u32 = 1000;

fn reset_below_hour(c: &mut Tm, usec: &mut i32) {
    c.hour = 0;
    c.min = 0;
    c.sec = 0;
    *usec = 0;
}

/// Walks the fields from year down to seconds, moving `tm` forward to the
/// first instant every field matches. Whenever a field has to change, all
/// smaller fields restart from their minimum; whenever a field has no match
/// left, the next larger field is bumped by one and the walk restarts.
pub fn find_next(spec: &CalendarSpec, clock: &mut Clock, tm: &mut Tm, usec: &mut i32) -> Result<(), Errno> {
    let mut c = *tm;
    let mut tm_usec = *usec;

    for _ in 0..MAX_CALENDAR_ITERATIONS {
        clock.mktime(&mut c);
        c.isdst = -1;

        // Year.
        let snapshot = c;
        let mut year = c.year + 1900;
        let r = find_matching_component(spec, &spec.year, false, &snapshot, clock, &mut year);
        c.year = year - 1900;
        match r {
            Match::Changed => {
                c.mon = 0;
                c.mday = 1;
                reset_below_hour(&mut c, &mut tm_usec);
            }
            Match::NoMatch => return Err(Errno::NoEnt),
            Match::Unchanged => {}
        }
        match tm_within_bounds(&mut c, clock) {
            Ok(Bounds::Exact) => {}
            _ => return Err(Errno::NoEnt),
        }

        // Month.
        let snapshot = c;
        let mut mon = c.mon + 1;
        let r = find_matching_component(spec, &spec.month, false, &snapshot, clock, &mut mon);
        c.mon = mon - 1;
        if let Match::Changed = r {
            c.mday = 1;
            reset_below_hour(&mut c, &mut tm_usec);
        }
        let b = match r {
            Match::NoMatch => Err(Errno::NoEnt),
            _ => tm_within_bounds(&mut c, clock),
        };
        match b {
            Err(_) => {
                c.year += 1;
                c.mon = 0;
                c.mday = 1;
                reset_below_hour(&mut c, &mut tm_usec);
                continue;
            }
            Ok(Bounds::Moved) => continue,
            Ok(Bounds::Exact) => {}
        }

        // Day of month.
        let snapshot = c;
        let mut mday = c.mday;
        let r = find_matching_component(spec, &spec.day, true, &snapshot, clock, &mut mday);
        c.mday = mday;
        if let Match::Changed = r {
            reset_below_hour(&mut c, &mut tm_usec);
        }
        let b = match r {
            Match::NoMatch => Err(Errno::NoEnt),
            _ => tm_within_bounds(&mut c, clock),
        };
        match b {
            Err(_) => {
                c.mon += 1;
                c.mday = 1;
                reset_below_hour(&mut c, &mut tm_usec);
                continue;
            }
            Ok(Bounds::Moved) => continue,
            Ok(Bounds::Exact) => {}
        }

        // Weekday.
        if !matches_weekday(spec.weekdays_bits, &c, clock) {
            c.mday += 1;
            reset_below_hour(&mut c, &mut tm_usec);
            continue;
        }

        // Hour.
        let snapshot = c;
        let mut hour = c.hour;
        let r = find_matching_component(spec, &spec.hour, false, &snapshot, clock, &mut hour);
        c.hour = hour;
        if let Match::Changed = r {
            c.min = 0;
            c.sec = 0;
            tm_usec = 0;
        }
        let b = match r {
            Match::NoMatch => Err(Errno::NoEnt),
            _ => tm_within_bounds(&mut c, clock),
        };
        match b {
            Err(_) => {
                c.mday += 1;
                reset_below_hour(&mut c, &mut tm_usec);
                continue;
            }
            // Folding changed the time; match again from there.
            Ok(Bounds::Moved) => continue,
            Ok(Bounds::Exact) => {}
        }

        // Minute.
        let snapshot = c;
        let mut min = c.min;
        let r = find_matching_component(spec, &spec.minute, false, &snapshot, clock, &mut min);
        c.min = min;
        if let Match::Changed = r {
            c.sec = 0;
            tm_usec = 0;
        }
        let b = match r {
            Match::NoMatch => Err(Errno::NoEnt),
            _ => tm_within_bounds(&mut c, clock),
        };
        match b {
            Err(_) => {
                c.hour += 1;
                c.min = 0;
                c.sec = 0;
                tm_usec = 0;
                continue;
            }
            Ok(Bounds::Moved) => continue,
            Ok(Bounds::Exact) => {}
        }

        // Second, with microseconds.
        let snapshot = c;
        let mut sec = c.sec * USEC_PER_SEC as i32 + tm_usec;
        let r = find_matching_component(spec, &spec.microsecond, false, &snapshot, clock, &mut sec);
        tm_usec = sec % USEC_PER_SEC as i32;
        c.sec = sec / USEC_PER_SEC as i32;
        let b = match r {
            Match::NoMatch => Err(Errno::NoEnt),
            _ => tm_within_bounds(&mut c, clock),
        };
        match b {
            Err(_) => {
                c.min += 1;
                c.sec = 0;
                tm_usec = 0;
                continue;
            }
            Ok(Bounds::Moved) => continue,
            Ok(Bounds::Exact) => {}
        }

        *tm = c;
        *usec = tm_usec;
        return Ok(());
    }

    Err(Errno::DeadLk)
}
