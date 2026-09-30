//! Broken-down calendar time, laid out like C's `struct tm`.
//!
//! Field ranges follow the C conventions on purpose: `year` counts from
//! 1900, `mon` is 0..=11, `wday` is 0 for Sunday. The elapse engine relies on
//! fields being allowed to go out of range and on `mktime` folding them back.

pub mod mktime;

pub const SECS_PER_DAY: i64 = 86_400;
pub const USEC_PER_SEC: i64 = 1_000_000;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct Tm {
    pub sec: i32,
    pub min: i32,
    pub hour: i32,
    pub mday: i32,
    pub mon: i32,
    pub year: i32,
    pub wday: i32,
    pub yday: i32,
    pub isdst: i32,
}

pub fn is_leap(full_year: i64) -> bool {
    full_year % 4 == 0 && (full_year % 100 != 0 || full_year % 400 == 0)
}

/// Cumulative day counts at the start of each month, `[leap][month]`.
pub const MON_YDAY: [[i32; 13]; 2] = [
    [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365],
    [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366],
];

pub fn days_in_month(full_year: i64, mon0: usize) -> i32 {
    let l = is_leap(full_year) as usize;
    MON_YDAY[l][mon0 + 1] - MON_YDAY[l][mon0]
}

/// Days since 1970-01-01 for a proleptic Gregorian date (month 1..=12).
pub fn days_from_civil(y: i64, m: i64, d: i64) -> i64 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = y - era * 400;
    let mp = (m + 9) % 12;
    let doy = (153 * mp + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + doe - 719_468
}

/// Inverse of [`days_from_civil`]; returns (year, month 1..=12, day).
pub fn civil_from_days(z: i64) -> (i64, i64, i64) {
    let z = z + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    (if m <= 2 { y + 1 } else { y }, m, d)
}

/// Breaks `t` seconds since the epoch down as wall time at a fixed UTC
/// offset (seconds east of Greenwich).
pub fn breakdown(t: i64, utoff: i64, isdst: i32) -> Tm {
    let local = t + utoff;
    let days = local.div_euclid(SECS_PER_DAY);
    let rem = local.rem_euclid(SECS_PER_DAY);
    let (y, m, d) = civil_from_days(days);
    let yday = days - days_from_civil(y, 1, 1);
    Tm {
        sec: (rem % 60) as i32,
        min: ((rem / 60) % 60) as i32,
        hour: (rem / 3600) as i32,
        mday: d as i32,
        mon: (m - 1) as i32,
        year: (y - 1900) as i32,
        wday: (days + 4).rem_euclid(7) as i32,
        yday: yday as i32,
        isdst,
    }
}

pub fn gmtime(t: i64) -> Tm {
    breakdown(t, 0, 0)
}
