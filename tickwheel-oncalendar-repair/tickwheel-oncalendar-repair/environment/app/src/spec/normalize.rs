use super::{CalendarSpec, Chain, Component, BITS_WEEKDAYS, MAX_YEAR, MIN_YEAR};
use crate::civil::USEC_PER_SEC;

fn normalize_chain(chain: &mut Chain) {
    let v = match chain {
        Some(v) => v,
        None => return,
    };

    for i in v.iter_mut() {
        if (i.stop > i.start && i.repeat > 0 && i.start + i.repeat > i.stop) || i.start == i.stop {
            i.repeat = 0;
            i.stop = -1;
        }
    }

    if v.len() <= 1 {
        return;
    }

    v.sort_by_key(|c| (c.start, c.stop, c.repeat));
    v.dedup();
}

/// Expands two-digit years to four digits.
fn fix_year(chain: &mut Chain) {
    if let Some(v) = chain {
        for c in v.iter_mut() {
            if c.start >= 0 && c.start < 100 {
                c.start += 2000;
            }
            if c.stop >= 0 && c.stop < 100 {
                c.stop += 2000;
            }
        }
    }
}

pub fn normalize(c: &mut CalendarSpec) {
    if c.timezone.as_deref() == Some("UTC") {
        c.utc = true;
        c.timezone = None;
    }

    if c.weekdays_bits <= 0 || c.weekdays_bits >= BITS_WEEKDAYS {
        c.weekdays_bits = -1;
    }

    if c.end_of_month && c.day.is_none() {
        c.end_of_month = false;
    }

    fix_year(&mut c.year);

    normalize_chain(&mut c.year);
    normalize_chain(&mut c.month);
    normalize_chain(&mut c.day);
    normalize_chain(&mut c.hour);
    normalize_chain(&mut c.minute);
    normalize_chain(&mut c.microsecond);
}

fn chain_valid(chain: &Chain, from: i32, to: i32, end_of_month: bool) -> bool {
    let v = match chain {
        Some(v) => v,
        None => return true,
    };

    let to = if end_of_month { to - 3 } else { to };

    v.iter().all(|c: &Component| {
        if c.start < from || c.start > to {
            return false;
        }
        if c.repeat > to - from {
            return false;
        }
        if c.stop >= 0 {
            if c.stop < from || c.stop > to {
                return false;
            }
            if c.start + c.repeat > c.stop {
                return false;
            }
        } else {
            if end_of_month && c.start - c.repeat < from {
                return false;
            }
            if !end_of_month && c.start + c.repeat > to {
                return false;
            }
        }
        true
    })
}

pub fn valid(c: &CalendarSpec) -> bool {
    if c.weekdays_bits > BITS_WEEKDAYS {
        return false;
    }
    chain_valid(&c.year, MIN_YEAR, MAX_YEAR, false)
        && chain_valid(&c.month, 1, 12, false)
        && chain_valid(&c.day, 1, 31, c.end_of_month)
        && chain_valid(&c.hour, 0, 23, false)
        && chain_valid(&c.minute, 0, 59, false)
        && chain_valid(&c.microsecond, 0, 60 * USEC_PER_SEC as i32 - 1, false)
}
