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

cat > src/spec/parse.rs <<'TW_SRC_SPEC_PARSE_RS'
use super::normalize::{normalize, valid};
use super::{CalendarSpec, Chain, Component, COMPONENTS_MAX};
use crate::civil::{gmtime, USEC_PER_SEC};
use crate::errno::Errno;
use crate::zone;

type Res<T> = Result<T, Errno>;

/// A byte cursor over the expression. `peek` yields 0 past the end so the
/// grammar can be written against a NUL terminated view of the text.
#[derive(Clone, Copy)]
struct Src<'a> {
    b: &'a [u8],
    p: usize,
}

impl<'a> Src<'a> {
    fn at(&self, off: usize) -> u8 {
        self.b.get(self.p + off).copied().unwrap_or(0)
    }

    fn peek(&self) -> u8 {
        self.at(0)
    }

    fn done(&self) -> bool {
        self.p >= self.b.len()
    }

    fn skip_spaces(&mut self) {
        while self.peek() == b' ' {
            self.p += 1;
        }
    }

    fn starts_with_no_case(&self, word: &str) -> bool {
        let w = word.as_bytes();
        self.b.len() >= self.p + w.len()
            && self.b[self.p..self.p + w.len()].eq_ignore_ascii_case(w)
    }
}

fn ends_with_no_case<'a>(s: &'a str, suffix: &str) -> Option<&'a str> {
    if s.len() < suffix.len() || !s.is_char_boundary(s.len() - suffix.len()) {
        return None;
    }
    let (head, tail) = s.split_at(s.len() - suffix.len());
    if tail.eq_ignore_ascii_case(suffix) {
        Some(head)
    } else {
        None
    }
}

const DAY_NAMES: [(&str, i32); 14] = [
    ("Monday", 0),
    ("Mon", 0),
    ("Tuesday", 1),
    ("Tue", 1),
    ("Wednesday", 2),
    ("Wed", 2),
    ("Thursday", 3),
    ("Thu", 3),
    ("Friday", 4),
    ("Fri", 4),
    ("Saturday", 5),
    ("Sat", 5),
    ("Sunday", 6),
    ("Sun", 6),
];

fn parse_weekdays(s: &mut Src, c: &mut CalendarSpec) -> Res<()> {
    let mut l: i32 = -1;
    let mut first = true;

    loop {
        let mut found: Option<i32> = None;
        for (name, nr) in DAY_NAMES.iter() {
            if !s.starts_with_no_case(name) {
                continue;
            }
            let skip = name.len();
            if !matches!(s.at(skip), 0 | b'-' | b'.' | b',' | b' ') {
                return Err(Errno::Inval);
            }

            c.weekdays_bits |= 1 << nr;

            if l >= 0 {
                if l > *nr {
                    return Err(Errno::Inval);
                }
                for j in (l + 1)..*nr {
                    c.weekdays_bits |= 1 << j;
                }
            }

            s.p += skip;
            found = Some(*nr);
            break;
        }

        let nr = match found {
            Some(n) => n,
            None => return if first { Ok(()) } else { Err(Errno::Inval) },
        };

        if s.done() {
            return Ok(());
        }

        if s.peek() == b' ' {
            s.skip_spaces();
            return Ok(());
        }

        if s.peek() == b'.' {
            if l >= 0 {
                return Err(Errno::Inval);
            }
            if s.at(1) != b'.' {
                return Err(Errno::Inval);
            }
            l = nr;
            s.p += 2;
        } else if s.peek() == b'-' {
            if l >= 0 {
                return Err(Errno::Inval);
            }
            l = nr;
            s.p += 1;
        } else if s.peek() == b',' {
            l = -1;
            s.p += 1;
        }

        if matches!(s.peek(), 0 | b' ') {
            s.skip_spaces();
            return if l < 0 { Ok(()) } else { Err(Errno::Inval) };
        }

        first = false;
    }
}

/// strtoul(3) restricted to what the grammar can reach: optional leading
/// white space and sign, then decimal digits.
fn parse_one_number(s: &mut Src) -> Res<u64> {
    let mut q = *s;
    while matches!(q.peek(), b' ' | b'\t' | b'\n' | b'\r' | 0x0b | 0x0c) {
        q.p += 1;
    }
    let neg = match q.peek() {
        b'-' => {
            q.p += 1;
            true
        }
        b'+' => {
            q.p += 1;
            false
        }
        _ => false,
    };
    if !q.peek().is_ascii_digit() {
        return Err(Errno::Inval);
    }
    let mut v: u64 = 0;
    let mut overflow = false;
    while q.peek().is_ascii_digit() {
        let d = (q.peek() - b'0') as u64;
        match v.checked_mul(10).and_then(|x| x.checked_add(d)) {
            Some(n) => v = n,
            None => overflow = true,
        }
        q.p += 1;
    }
    if overflow {
        return Err(Errno::Range);
    }
    s.p = q.p;
    Ok(if neg { v.wrapping_neg() } else { v })
}

fn parse_fractional_part_u(s: &mut Src, digits: usize) -> Res<u32> {
    let mut val: u32 = 0;
    let mut q = *s;
    let mut i = 0;
    while i < digits {
        if !q.peek().is_ascii_digit() {
            if i == 0 {
                return Err(Errno::Inval);
            }
            while i < digits {
                val *= 10;
                i += 1;
            }
            break;
        }
        val = val * 10 + (q.peek() - b'0') as u32;
        q.p += 1;
        i += 1;
    }
    if (b'5'..=b'9').contains(&q.peek()) {
        val += 1;
    }
    while q.peek().is_ascii_digit() {
        q.p += 1;
    }
    s.p = q.p;
    Ok(val)
}

fn parse_component_decimal(s: &mut Src, usec: bool) -> Res<i32> {
    if !s.peek().is_ascii_digit() {
        return Err(Errno::Inval);
    }
    let mut e = *s;
    let mut value = parse_one_number(&mut e)?;

    if usec {
        value = value.checked_mul(USEC_PER_SEC as u64).ok_or(Errno::Range)?;
        if e.peek() == b'.' && e.at(1) != b'.' {
            e.p += 1;
            let add = parse_fractional_part_u(&mut e, 6)? as u64;
            value = value.checked_add(add).ok_or(Errno::Range)?;
        }
    }

    if value > i32::MAX as u64 {
        return Err(Errno::Range);
    }
    s.p = e.p;
    Ok(value as i32)
}

fn prepend_component(s: &mut Src, usec: bool, nesting: usize, chain: &mut Vec<Component>) -> Res<()> {
    if nesting > COMPONENTS_MAX {
        return Err(Errno::NoBufs);
    }

    let mut e = *s;
    let start = parse_component_decimal(&mut e, usec)?;
    let mut stop = -1;
    let mut repeat = 0;

    if e.peek() == b'.' && e.at(1) == b'.' {
        e.p += 2;
        stop = parse_component_decimal(&mut e, usec)?;
        repeat = if usec { USEC_PER_SEC as i32 } else { 1 };
    }

    if e.peek() == b'/' {
        e.p += 1;
        repeat = parse_component_decimal(&mut e, usec)?;
        if repeat == 0 {
            return Err(Errno::Range);
        }
    } else {
        if start > i32::MAX - repeat {
            return Err(Errno::Range);
        }
        if usec && stop >= 0 && start + repeat > stop {
            return Err(Errno::Inval);
        }
    }

    if !matches!(e.peek(), 0 | b' ' | b',' | b'-' | b'~' | b':') {
        return Err(Errno::Inval);
    }

    chain.insert(0, Component { start, stop, repeat });
    s.p = e.p;

    if e.peek() == b',' {
        s.p += 1;
        return prepend_component(s, usec, nesting + 1, chain);
    }
    Ok(())
}

fn parse_chain(s: &mut Src, usec: bool) -> Res<Chain> {
    if s.peek() == b'*' {
        s.p += 1;
        if usec {
            return Ok(Some(vec![Component { start: 0, stop: -1, repeat: USEC_PER_SEC as i32 }]));
        }
        return Ok(None);
    }
    let mut v = Vec::new();
    prepend_component(s, usec, 0, &mut v)?;
    Ok(Some(v))
}

fn from_time_t(c: &mut CalendarSpec, t: i64) -> Res<()> {
    if !(-67_768_040_609_740_800..=67_767_976_233_316_799).contains(&t) {
        return Err(Errno::Range);
    }
    let tm = gmtime(t);
    c.utc = true;
    c.year = Some(vec![Component::single(tm.year + 1900)]);
    c.month = Some(vec![Component::single(tm.mon + 1)]);
    c.day = Some(vec![Component::single(tm.mday)]);
    c.hour = Some(vec![Component::single(tm.hour)]);
    c.minute = Some(vec![Component::single(tm.min)]);
    c.microsecond = Some(vec![Component::single(tm.sec * USEC_PER_SEC as i32)]);
    Ok(())
}

/// Returns true when the expression was a complete `@epoch` form and no
/// time of day follows.
fn parse_date(s: &mut Src, c: &mut CalendarSpec) -> Res<bool> {
    let mut t = *s;
    if t.done() {
        return Ok(false);
    }

    if t.peek() == b'@' {
        t.p += 1;
        let value = parse_one_number(&mut t)?;
        from_time_t(c, value as i64)?;
        s.p = t.p;
        return Ok(true);
    }

    let first = parse_chain(&mut t, false)?;

    if matches!(t.peek(), 0 | b':') {
        return Ok(false);
    }

    if t.peek() == b'~' {
        c.end_of_month = true;
    } else if t.peek() != b'-' {
        return Err(Errno::Inval);
    }

    t.p += 1;
    let second = parse_chain(&mut t, false)?;

    if matches!(t.peek(), 0 | b' ') {
        t.skip_spaces();
        s.p = t.p;
        c.month = first;
        c.day = second;
        return Ok(false);
    } else if c.end_of_month {
        return Err(Errno::Inval);
    }

    if t.peek() == b'~' {
        c.end_of_month = true;
    } else if t.peek() != b'-' {
        return Err(Errno::Inval);
    }

    t.p += 1;
    let third = parse_chain(&mut t, false)?;

    if !matches!(t.peek(), 0 | b' ') {
        return Err(Errno::Inval);
    }

    t.skip_spaces();
    s.p = t.p;
    c.year = first;
    c.month = second;
    c.day = third;
    Ok(false)
}

fn parse_calendar_time(s: &mut Src, c: &mut CalendarSpec) -> Res<()> {
    let mut t = *s;

    if t.done() {
        c.hour = Some(vec![Component::single(0)]);
        c.minute = Some(vec![Component::single(0)]);
        c.microsecond = Some(vec![Component::single(0)]);
        return Ok(());
    }

    let h = parse_chain(&mut t, false)?;
    if t.peek() != b':' {
        return Err(Errno::Inval);
    }
    t.p += 1;
    let m = parse_chain(&mut t, false)?;

    let sec = if t.done() {
        Some(vec![Component::single(0)])
    } else {
        if t.peek() != b':' {
            return Err(Errno::Inval);
        }
        t.p += 1;
        let sec = parse_chain(&mut t, true)?;
        if !t.done() {
            return Err(Errno::Inval);
        }
        sec
    };

    s.p = t.p;
    c.hour = h;
    c.minute = m;
    c.microsecond = sec;
    Ok(())
}

fn zero_time(c: &mut CalendarSpec, with_hour: bool, with_minute: bool) {
    if with_hour {
        c.hour = Some(vec![Component::single(0)]);
    }
    if with_minute {
        c.minute = Some(vec![Component::single(0)]);
    }
    c.microsecond = Some(vec![Component::single(0)]);
}

fn months(list: &[i32]) -> Chain {
    Some(list.iter().rev().map(|&m| Component::single(m)).collect())
}

pub fn parse(input: &str) -> Res<CalendarSpec> {
    let mut c = CalendarSpec::default();

    let body: &str = if let Some(head) = ends_with_no_case(input, " UTC") {
        c.utc = true;
        head
    } else {
        match input.rfind(' ') {
            Some(i) if zone::is_valid_name(&input[i + 1..]) => {
                c.timezone = Some(input[i + 1..].to_string());
                &input[..i]
            }
            _ => input,
        }
    };

    if body.is_empty() {
        return Err(Errno::Inval);
    }

    let lower = body.to_ascii_lowercase();
    match lower.as_str() {
        "minutely" => zero_time(&mut c, false, false),
        "hourly" => zero_time(&mut c, false, true),
        "daily" => zero_time(&mut c, true, true),
        "monthly" => {
            c.day = Some(vec![Component::single(1)]);
            zero_time(&mut c, true, true);
        }
        "annually" | "yearly" | "anually" => {
            c.month = Some(vec![Component::single(1)]);
            c.day = Some(vec![Component::single(1)]);
            zero_time(&mut c, true, true);
        }
        "weekly" => {
            c.weekdays_bits = 1;
            zero_time(&mut c, true, true);
        }
        "quarterly" => {
            c.month = months(&[1, 4, 7, 10]);
            c.day = Some(vec![Component::single(1)]);
            zero_time(&mut c, true, true);
        }
        "biannually" | "bi-annually" | "semiannually" | "semi-annually" => {
            c.month = months(&[1, 7]);
            c.day = Some(vec![Component::single(1)]);
            zero_time(&mut c, true, true);
        }
        _ => {
            let mut s = Src { b: body.as_bytes(), p: 0 };
            parse_weekdays(&mut s, &mut c)?;
            let epoch = parse_date(&mut s, &mut c)?;
            if !epoch {
                parse_calendar_time(&mut s, &mut c)?;
            }
            if !s.done() {
                return Err(Errno::Inval);
            }
        }
    }

    normalize(&mut c);

    if !valid(&c) {
        return Err(Errno::Inval);
    }
    Ok(c)
}
TW_SRC_SPEC_PARSE_RS


cargo build --release --offline
tickwheel calendar --base-time='2026-03-28 12:00:00 UTC' --iterations=3 '*-*-* 02:30 Europe/Berlin' 'Sat,Sun 10:00'
