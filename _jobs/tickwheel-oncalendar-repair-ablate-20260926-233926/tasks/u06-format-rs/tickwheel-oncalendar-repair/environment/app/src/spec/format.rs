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
                out.push_str("..");
                out.push_str(DAYS[(x - 1) as usize]);
            }
            l = -1;
        }
        x += 1;
    }

    if l >= 0 && x > l + 1 {
        out.push_str("..");
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
