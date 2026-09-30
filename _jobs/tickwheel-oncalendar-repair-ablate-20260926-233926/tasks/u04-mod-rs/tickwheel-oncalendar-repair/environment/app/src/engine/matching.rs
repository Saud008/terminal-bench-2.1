use super::Clock;
use crate::civil::Tm;
use crate::spec::{CalendarSpec, Chain};

/// Day of month that is `day` days before the start of the following month
/// (so `day == 1` is the last day), or -1 if that falls outside the month.
pub fn find_end_of_month(tm: &Tm, clock: &mut Clock, day: i32) -> i32 {
    let mut t = *tm;
    t.mon += 1;
    t.mday = 1 - day;

    if clock.mktime(&mut t) < 0 || t.mon != tm.mon {
        return -1;
    }
    t.mday
}

pub enum Match {
    Unchanged,
    Changed,
    NoMatch,
}

/// Earliest value >= `*val` produced by any element of `chain`, written
/// back to `*val`. `tm` is only consulted for `~` (end of month) days.
pub fn find_matching_component(
    spec: &CalendarSpec,
    chain: &Chain,
    is_day: bool,
    tm: &Tm,
    clock: &mut Clock,
    val: &mut i32,
) -> Match {
    let v = match chain {
        None => return Match::Unchanged,
        Some(v) => v,
    };

    let end_of_month = spec.end_of_month && is_day;
    let mut d: Option<i32> = None;

    for c in v {
        let (mut start, mut stop) = (c.start, c.stop);

        if end_of_month {
            start = find_end_of_month(tm, clock, c.start);
            stop = find_end_of_month(tm, clock, c.stop);
        }

        if start >= *val {
            if d.map_or(true, |x| start < x) {
                d = Some(start);
            }
        } else if c.repeat > 0 {
            let k = start + c.repeat * ((*val - start + c.repeat - 1) / c.repeat);
            if d.map_or(true, |x| k < x) && (stop < 0 || k <= stop) {
                d = Some(k);
            }
        }
    }

    match d {
        None => Match::NoMatch,
        Some(x) => {
            let changed = *val != x;
            *val = x;
            if changed {
                Match::Changed
            } else {
                Match::Unchanged
            }
        }
    }
}
