#!/bin/bash
set -euo pipefail

cd /app

cat > src/civil/mktime.rs <<'TW_SRC_CIVIL_MKTIME_RS'
//! Wall time to epoch conversion with the same probing strategy as the GNU
//! C library's `mktime`.
//!
//! The conversion inverts `localtime` by repeated guessing. The guess starts
//! from the caller's `offset` hint, which is updated on success; which of two
//! candidate instants an ambiguous or nonexistent wall time resolves to
//! depends on it (see docs/timezones.md).

use super::{is_leap, Tm, MON_YDAY};
use crate::zone::Zone;

const TM_YEAR_BASE: i64 = 1900;
const EPOCH_YEAR: i64 = 1970;

fn shr(a: i64, b: u32) -> i64 {
    a >> b
}

fn leapyear(year: i64) -> usize {
    is_leap(year + TM_YEAR_BASE) as usize
}

fn isdst_differ(a: i32, b: i32) -> bool {
    ((a == 0) != (b == 0)) && a >= 0 && b >= 0
}

#[allow(clippy::too_many_arguments)]
fn ydhms_diff(
    year1: i64,
    yday1: i64,
    hour1: i64,
    min1: i64,
    sec1: i64,
    year0: i64,
    yday0: i64,
    hour0: i64,
    min0: i64,
    sec0: i64,
) -> i64 {
    let a4 = shr(year1, 2) + shr(TM_YEAR_BASE, 2) - ((year1 & 3) == 0) as i64;
    let b4 = shr(year0, 2) + shr(TM_YEAR_BASE, 2) - ((year0 & 3) == 0) as i64;
    let a100 = (a4 + (a4 < 0) as i64) / 25 - (a4 < 0) as i64;
    let b100 = (b4 + (b4 < 0) as i64) / 25 - (b4 < 0) as i64;
    let a400 = shr(a100, 2);
    let b400 = shr(b100, 2);
    let intervening_leap_days = (a4 - b4) - (a100 - b100) + (a400 - b400);

    let years = year1 - year0;
    let days = 365 * years + yday1 - yday0 + intervening_leap_days;
    let hours = 24 * days + hour1 - hour0;
    let minutes = 60 * hours + min1 - min0;
    60 * minutes + sec1 - sec0
}

fn tm_diff(year: i64, yday: i64, hour: i64, min: i64, sec: i64, tp: &Tm) -> i64 {
    ydhms_diff(
        year,
        yday,
        hour,
        min,
        sec,
        tp.year as i64,
        tp.yday as i64,
        tp.hour as i64,
        tp.min as i64,
        tp.sec as i64,
    )
}

/// Converts `*tp` to seconds since the epoch in `zone`, normalising `*tp`
/// on success. Returns -1 and leaves `*tp` untouched on failure.
pub fn mktime(tp: &mut Tm, zone: &Zone, offset: &mut i64) -> i64 {
    let mut remaining_probes = 6;

    let mut sec = tp.sec as i64;
    let min = tp.min as i64;
    let hour = tp.hour as i64;
    let mday = tp.mday as i64;
    let mon = tp.mon;
    let year_requested = tp.year as i64;
    let isdst = tp.isdst;

    let mut dst2: i32 = 0;

    let mon_remainder = mon % 12;
    let negative_mon_remainder = (mon_remainder < 0) as i32;
    let mon_years = (mon / 12 - negative_mon_remainder) as i64;
    let year = year_requested + mon_years;

    let mon_yday = MON_YDAY[leapyear(year)][(mon_remainder + 12 * negative_mon_remainder) as usize]
        as i64
        - 1;
    let yday = mon_yday + mday;

    let off = *offset;
    let negative_offset_guess = off.wrapping_neg();

    let sec_requested = sec;
    if sec < 0 {
        sec = 0;
    }
    if sec > 59 {
        sec = 59;
    }

    let t0 = ydhms_diff(
        year,
        yday,
        hour,
        min,
        sec,
        EPOCH_YEAR - TM_YEAR_BASE,
        0,
        0,
        0,
        negative_offset_guess,
    );
    let (mut t, mut t1, mut t2) = (t0, t0, t0);
    let mut tm: Tm;

    'probe: {
        loop {
            tm = zone.localtime(t);
            let dt = tm_diff(year, yday, hour, min, sec, &tm);
            if dt == 0 {
                break;
            }

            if t == t1
                && t != t2
                && (tm.isdst < 0
                    || (if isdst < 0 {
                        dst2 <= (tm.isdst != 0) as i32
                    } else {
                        (isdst != 0) != (tm.isdst != 0)
                    }))
            {
                break 'probe;
            }

            remaining_probes -= 1;
            if remaining_probes == 0 {
                return -1;
            }

            t1 = t2;
            t2 = t;
            t += dt;
            dst2 = (tm.isdst != 0) as i32;
        }

        if isdst_differ(isdst, tm.isdst) {
            // +1 if standard time was asked for but DST came out, -1 for the
            // reverse; used when no time with the requested flag is nearby.
            let dst_difference = (isdst == 0) as i64 - (tm.isdst == 0) as i64;
            let stride: i64 = 601_200;
            let duration_max: i64 = 457_243_209;
            let delta_bound = duration_max / 2 + stride;
            let mut delta = stride;
            while delta < delta_bound {
                for direction in [-1i64, 1] {
                    let ot = t + delta * direction;
                    let otm = zone.localtime(ot);
                    if !isdst_differ(isdst, otm.isdst) {
                        let gt = ot + tm_diff(year, yday, hour, min, sec, &otm);
                        tm = zone.localtime(gt);
                        t = gt;
                        break 'probe;
                    }
                }
                delta += stride;
            }
            t += 3600 * dst_difference;
            tm = zone.localtime(t);
            break 'probe;
        }
    }

    *offset = t.wrapping_sub(t0).wrapping_sub(negative_offset_guess);

    if sec_requested != tm.sec as i64 {
        let mut sec_adjustment = (sec == 0 && tm.sec == 60) as i64;
        sec_adjustment -= sec;
        sec_adjustment += sec_requested;
        t += sec_adjustment;
        tm = zone.localtime(t);
    }

    *tp = tm;
    t
}
TW_SRC_CIVIL_MKTIME_RS

cat > src/engine/bounds.rs <<'TW_SRC_ENGINE_BOUNDS_RS'
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

/// Folds out-of-range fields (June 31st, hour 24, a wall time skipped by a
/// clock change, ...) and reports whether that moved the time.
///
/// When a larger unit changed, the next smaller unit of the folded time is
/// reset so no candidate between the old and the new value is lost.
pub fn tm_within_bounds(tm: &mut Tm, clock: &mut Clock) -> Result<Bounds, Errno> {
    if tm.year + 1900 > MAX_YEAR {
        return Err(Errno::Range);
    }

    let mut t = *tm;
    if clock.mktime(&mut t) < 0 {
        return Err(Errno::Overflow);
    }

    use std::cmp::Ordering;
    let mut cmp = t.year.cmp(&tm.year);
    if cmp != Ordering::Equal {
        t.mon = 0;
    } else {
        cmp = t.mon.cmp(&tm.mon);
        if cmp != Ordering::Equal {
            t.mday = 1;
        } else {
            cmp = t.mday.cmp(&tm.mday);
            if cmp != Ordering::Equal {
                t.hour = 0;
            } else {
                cmp = t.hour.cmp(&tm.hour);
                if cmp != Ordering::Equal {
                    t.min = 0;
                } else {
                    cmp = t.min.cmp(&tm.min);
                    if cmp != Ordering::Equal {
                        t.sec = 0;
                    } else {
                        cmp = t.sec.cmp(&tm.sec);
                    }
                }
            }
        }
    }

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
TW_SRC_ENGINE_BOUNDS_RS

cat > src/engine/matching.rs <<'TW_SRC_ENGINE_MATCHING_RS'
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
            if stop > 0 {
                std::mem::swap(&mut start, &mut stop);
            }
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
TW_SRC_ENGINE_MATCHING_RS

cat > src/engine/mod.rs <<'TW_SRC_ENGINE_MOD_RS'
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

/// Wall clock used while evaluating one expression. The `offset` hint is
/// shared by every wall-time conversion of a single next-elapse computation
/// and starts from zero for each computation.
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
        mktime(tm, &self.zone, &mut self.offset)
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
TW_SRC_ENGINE_MOD_RS

cat > src/engine/next.rs <<'TW_SRC_ENGINE_NEXT_RS'
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
    let mut keep_isdst = false;

    for _ in 0..MAX_CALENDAR_ITERATIONS {
        clock.mktime(&mut c);
        if !keep_isdst {
            c.isdst = -1;
        }

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

        // A wall time that folds back onto (or before) the starting point
        // can't be the answer. Step an hour on and let the conversion pick
        // the offset from then on instead of forcing "unknown".
        if (tm.year, tm.mon, tm.mday, tm.hour, tm.min, tm.sec, *usec)
            >= (c.year, c.mon, c.mday, c.hour, c.min, c.sec, tm_usec + 1)
        {
            keep_isdst = true;
            c.hour += 1;
            continue;
        }

        *tm = c;
        *usec = tm_usec;
        return Ok(());
    }

    Err(Errno::DeadLk)
}
TW_SRC_ENGINE_NEXT_RS

cat > src/spec/format.rs <<'TW_SRC_SPEC_FORMAT_RS'
use super::{CalendarSpec, Chain, Component, BITS_WEEKDAYS};
use crate::civil::USEC_PER_SEC;
use std::fmt::Write;

const DAYS: [&str; 7] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

fn format_weekdays(out: &mut String, bits: i32) {
    let mut need_comma = false;
    let mut l: i32 = -1;
    let mut x: i32 = 0;

    while x < DAYS.len() as i32 {
        if bits & (1 << x) != 0 {
            if l < 0 {
                if need_comma {
                    out.push(',');
                } else {
                    need_comma = true;
                }
                out.push_str(DAYS[x as usize]);
                l = x;
            }
        } else if l >= 0 {
            if x > l + 1 {
                out.push_str(if x > l + 2 { ".." } else { "," });
                out.push_str(DAYS[(x - 1) as usize]);
            }
            l = -1;
        }
        x += 1;
    }

    if l >= 0 && x > l + 1 {
        out.push_str(if x > l + 2 { ".." } else { "," });
        out.push_str(DAYS[(x - 1) as usize]);
    }
}

fn chain_is_star(chain: &Chain, usec: bool) -> bool {
    match chain {
        None => true,
        Some(v) => {
            usec && v.iter().any(|c| c.start == 0 && c.stop < 0 && c.repeat == USEC_PER_SEC as i32)
        }
    }
}

fn format_component(out: &mut String, width: usize, c: &Component, usec: bool) {
    let d = if usec { USEC_PER_SEC as i32 } else { 1 };

    let _ = write!(out, "{:0w$}", c.start / d, w = width);
    if c.start % d > 0 {
        let _ = write!(out, ".{:06}", c.start % d);
    }

    if c.stop > 0 {
        let _ = write!(out, "..{:0w$}", c.stop / d, w = width);
    }
    if c.stop % d > 0 {
        let _ = write!(out, ".{:06}", c.stop % d);
    }

    if c.repeat > 0 && !(c.stop > 0 && c.repeat == d) {
        let _ = write!(out, "/{}", c.repeat / d);
    }
    if c.repeat % d > 0 {
        let _ = write!(out, ".{:06}", c.repeat % d);
    }
}

fn format_chain(out: &mut String, width: usize, chain: &Chain, usec: bool) {
    if chain_is_star(chain, usec) {
        out.push('*');
        return;
    }
    let v = chain.as_ref().expect("non-star chain");
    for (i, c) in v.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        format_component(out, width, c, usec);
    }
}

pub fn to_string(c: &CalendarSpec) -> String {
    let mut out = String::new();

    if c.weekdays_bits > 0 && c.weekdays_bits <= BITS_WEEKDAYS {
        format_weekdays(&mut out, c.weekdays_bits);
        out.push(' ');
    }

    format_chain(&mut out, 4, &c.year, false);
    out.push('-');
    format_chain(&mut out, 2, &c.month, false);
    out.push(if c.end_of_month { '~' } else { '-' });
    format_chain(&mut out, 2, &c.day, false);
    out.push(' ');
    format_chain(&mut out, 2, &c.hour, false);
    out.push(':');
    format_chain(&mut out, 2, &c.minute, false);
    out.push(':');
    format_chain(&mut out, 2, &c.microsecond, true);

    if c.utc {
        out.push_str(" UTC");
    } else if let Some(tz) = &c.timezone {
        out.push(' ');
        out.push_str(tz);
    }
    out
}
TW_SRC_SPEC_FORMAT_RS

cat > src/spec/normalize.rs <<'TW_SRC_SPEC_NORMALIZE_RS'
use super::{CalendarSpec, Chain, Component, BITS_WEEKDAYS, MAX_YEAR, MIN_YEAR};
use crate::civil::USEC_PER_SEC;

fn normalize_chain(chain: &mut Chain) {
    let v = match chain {
        Some(v) => v,
        None => return,
    };

    for i in v.iter_mut() {
        if i.stop > i.start && i.repeat > 0 {
            i.stop -= (i.stop - i.start) % i.repeat;
        }

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

/// Two digit years: 00..69 are 20xx, 70..99 are 19xx.
fn fix_year(chain: &mut Chain) {
    if let Some(v) = chain {
        for c in v.iter_mut() {
            if c.start >= 0 && c.start < 70 {
                c.start += 2000;
            }
            if c.stop >= 0 && c.stop < 70 {
                c.stop += 2000;
            }
            if c.start >= 70 && c.start < 100 {
                c.start += 1900;
            }
            if c.stop >= 70 && c.stop < 100 {
                c.stop += 1900;
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
TW_SRC_SPEC_NORMALIZE_RS


cat > src/zone/rule.rs <<'TW_SRC_ZONE_RULE_RS'
//! POSIX TZ strings as found in the TZif footer, e.g.
//! `CET-1CEST,M3.5.0,M10.5.0/3`. Used for instants after the last
//! transition stored in the file.

use crate::civil::{days_from_civil, gmtime, is_leap, SECS_PER_DAY};

#[derive(Debug, Clone, Copy)]
enum When {
    /// Jn: day 1..=365, February 29 never counted.
    Julian1(i64),
    /// n: day 0..=365, February 29 counted in leap years.
    Julian0(i64),
    /// Mm.w.d
    Month { m: i64, w: i64, d: i64 },
}

#[derive(Debug, Clone, Copy)]
struct Change {
    when: When,
    secs: i64,
}

#[derive(Debug, Clone)]
pub struct PosixRule {
    std_off: i64,
    dst: Option<(i64, Change, Change)>,
}

struct Cursor<'a> {
    s: &'a [u8],
    p: usize,
}

impl<'a> Cursor<'a> {
    fn peek(&self) -> Option<u8> {
        self.s.get(self.p).copied()
    }

    fn eat(&mut self, c: u8) -> bool {
        if self.peek() == Some(c) {
            self.p += 1;
            true
        } else {
            false
        }
    }

    fn name(&mut self) -> Option<()> {
        if self.eat(b'<') {
            while self.peek()? != b'>' {
                self.p += 1;
            }
            self.p += 1;
            return Some(());
        }
        let start = self.p;
        while matches!(self.peek(), Some(c) if c.is_ascii_alphabetic()) {
            self.p += 1;
        }
        if self.p - start < 3 {
            return None;
        }
        Some(())
    }

    fn number(&mut self) -> Option<i64> {
        let start = self.p;
        let mut v: i64 = 0;
        while let Some(c) = self.peek() {
            if !c.is_ascii_digit() {
                break;
            }
            v = v * 10 + (c - b'0') as i64;
            self.p += 1;
        }
        if self.p == start {
            None
        } else {
            Some(v)
        }
    }

    /// [+-]hh[:mm[:ss]] in seconds.
    fn hms(&mut self) -> Option<i64> {
        let neg = if self.eat(b'-') {
            true
        } else {
            self.eat(b'+');
            false
        };
        let mut v = self.number()? * 3600;
        if self.eat(b':') {
            v += self.number()? * 60;
            if self.eat(b':') {
                v += self.number()?;
            }
        }
        Some(if neg { -v } else { v })
    }

    fn change(&mut self) -> Option<Change> {
        let when = if self.eat(b'J') {
            When::Julian1(self.number()?)
        } else if self.eat(b'M') {
            let m = self.number()?;
            if !self.eat(b'.') {
                return None;
            }
            let w = self.number()?;
            if !self.eat(b'.') {
                return None;
            }
            let d = self.number()?;
            When::Month { m, w, d }
        } else {
            When::Julian0(self.number()?)
        };
        let secs = if self.eat(b'/') { self.hms()? } else { 7200 };
        Some(Change { when, secs })
    }
}

impl PosixRule {
    pub fn parse(s: &str) -> Option<PosixRule> {
        let mut c = Cursor { s: s.as_bytes(), p: 0 };
        c.name()?;
        let std_off = -c.hms()?;
        if c.peek().is_none() {
            return Some(PosixRule { std_off, dst: None });
        }
        c.name()?;
        let dst_off = match c.peek() {
            Some(b',') | None => std_off + 3600,
            _ => -c.hms()?,
        };
        if !c.eat(b',') {
            return None;
        }
        let start = c.change()?;
        if !c.eat(b',') {
            return None;
        }
        let end = c.change()?;
        if c.peek().is_some() {
            return None;
        }
        Some(PosixRule { std_off, dst: Some((dst_off, start, end)) })
    }

    /// UTC instant at which `ch` happens in `year`, given the offset in
    /// effect just before it.
    fn change_time(ch: &Change, year: i64, off_before: i64) -> i64 {
        let jan1 = days_from_civil(year, 1, 1) * SECS_PER_DAY;
        let day = match ch.when {
            When::Julian1(n) => {
                let mut d = n - 1;
                if n >= 60 && is_leap(year) {
                    d += 1;
                }
                d
            }
            When::Julian0(n) => n,
            When::Month { m, w, d } => {
                let first = days_from_civil(year, m, 1);
                let dow_first = (first + 4).rem_euclid(7);
                let mut mday0 = (d - dow_first).rem_euclid(7);
                let dim = crate::civil::days_in_month(year, (m - 1) as usize) as i64;
                for _ in 1..w {
                    if mday0 + 7 >= dim {
                        break;
                    }
                    mday0 += 7;
                }
                first - days_from_civil(year, 1, 1) + mday0
            }
        };
        jan1 + day * SECS_PER_DAY + ch.secs - off_before
    }

    /// (seconds east of UTC, is DST) at instant `t`.
    pub fn offset_at(&self, t: i64) -> (i64, bool) {
        let (dst_off, start, end) = match &self.dst {
            None => return (self.std_off, false),
            Some(d) => *d,
        };
        let year = gmtime(t).year as i64 + 1900;
        let c0 = Self::change_time(&start, year, self.std_off);
        let c1 = Self::change_time(&end, year, dst_off);
        let isdst = if c0 > c1 { t < c1 || t >= c0 } else { t >= c0 && t < c1 };
        if isdst {
            (dst_off, true)
        } else {
            (self.std_off, false)
        }
    }
}
TW_SRC_ZONE_RULE_RS

cargo build --release --offline
tickwheel calendar --base-time='2026-03-28 12:00:00 UTC' --iterations=3 '*-*-* 02:30 Europe/Berlin' 'Sat,Sun 10:00'
