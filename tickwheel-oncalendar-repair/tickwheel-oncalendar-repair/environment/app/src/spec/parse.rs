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
                let mut j = (l + 1) % 7;
                while j != *nr {
                    c.weekdays_bits |= 1 << j;
                    j = (j + 1) % 7;
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
        if s.peek() == b'/' {
            s.p += 1;
            let repeat = parse_component_decimal(s, usec)?;
            if repeat == 0 {
                return Err(Errno::Range);
            }
            return Ok(Some(vec![Component { start: 0, stop: -1, repeat }]));
        }
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
