//! Base-time parsing and elapse formatting. Everything is UTC.

use crate::civil::{days_from_civil, days_in_month, gmtime, SECS_PER_DAY, USEC_PER_SEC};

const WDAY: [&str; 7] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/// `Sat 2026-03-28 12:20:00 UTC`; sub-second parts are not shown.
pub fn format_utc(usec: u64) -> String {
    let tm = gmtime((usec / USEC_PER_SEC as u64) as i64);
    format!(
        "{} {:04}-{:02}-{:02} {:02}:{:02}:{:02} UTC",
        WDAY[tm.wday as usize],
        tm.year + 1900,
        tm.mon + 1,
        tm.mday,
        tm.hour,
        tm.min,
        tm.sec
    )
}

fn num(s: &str, len: usize) -> Option<i64> {
    if s.len() != len || !s.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }
    s.parse().ok()
}

/// Accepts `@SECONDS`, `YYYY-MM-DD`, `YYYY-MM-DD HH:MM` and
/// `YYYY-MM-DD HH:MM:SS`, each optionally followed by ` UTC`.
/// Returns microseconds since the epoch.
pub fn parse_base_time(s: &str) -> Option<u64> {
    if let Some(rest) = s.strip_prefix('@') {
        if rest.is_empty() || !rest.bytes().all(|b| b.is_ascii_digit()) {
            return None;
        }
        let secs: u64 = rest.parse().ok()?;
        return secs.checked_mul(USEC_PER_SEC as u64);
    }

    let s = s.strip_suffix(" UTC").unwrap_or(s);
    let (date, time) = match s.split_once(' ') {
        Some((d, t)) => (d, Some(t)),
        None => (s, None),
    };

    let mut dp = date.split('-');
    let y = num(dp.next()?, 4)?;
    let m = num(dp.next()?, 2)?;
    let d = num(dp.next()?, 2)?;
    if dp.next().is_some() || !(1970..=9999).contains(&y) || !(1..=12).contains(&m) {
        return None;
    }
    if d < 1 || d > days_in_month(y, (m - 1) as usize) as i64 {
        return None;
    }

    let (hh, mm, ss) = match time {
        None => (0, 0, 0),
        Some(t) => {
            let parts: Vec<&str> = t.split(':').collect();
            match parts.as_slice() {
                [h, mi] => (num(h, 2)?, num(mi, 2)?, 0),
                [h, mi, se] => (num(h, 2)?, num(mi, 2)?, num(se, 2)?),
                _ => return None,
            }
        }
    };
    if hh > 23 || mm > 59 || ss > 59 {
        return None;
    }

    let secs = days_from_civil(y, m, d) * SECS_PER_DAY + hh * 3600 + mm * 60 + ss;
    Some(secs as u64 * USEC_PER_SEC as u64)
}
