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
                        dst2 >= (tm.isdst != 0) as i32
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
