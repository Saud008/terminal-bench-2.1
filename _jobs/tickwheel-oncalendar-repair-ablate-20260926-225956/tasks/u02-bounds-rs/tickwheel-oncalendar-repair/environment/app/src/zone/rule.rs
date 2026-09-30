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
                    if mday0 + 7 > dim {
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
