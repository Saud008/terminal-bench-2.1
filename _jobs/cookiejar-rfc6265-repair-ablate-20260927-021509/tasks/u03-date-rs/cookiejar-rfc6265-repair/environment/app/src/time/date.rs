//! The cookie-date parser (RFC 6265 section 5.1.1). It accepts far more than
//! the three formats servers are supposed to send.

use super::civil::timestamp;

const MONTHS: [&[u8; 3]; 12] = [
    b"jan", b"feb", b"mar", b"apr", b"may", b"jun", b"jul", b"aug", b"sep", b"oct", b"nov", b"dec",
];

fn is_delimiter(b: u8) -> bool {
    b == 0x09
        || (0x20..=0x2f).contains(&b)
        || (0x3b..=0x40).contains(&b)
        || (0x5b..=0x60).contains(&b)
        || (0x7b..=0x7e).contains(&b)
}

/// `min*maxDIGIT ( non-digit *OCTET )`: the value of the leading digits and
/// whatever follows them.
fn digits(tok: &[u8], min: usize, max: usize) -> Option<(i64, &[u8])> {
    let n = tok.iter().take_while(|b| b.is_ascii_digit()).count();
    if n < min || n > max {
        return None;
    }
    let v = tok[..n].iter().fold(0i64, |acc, b| acc * 10 + i64::from(b - b'0'));
    Some((v, &tok[n..]))
}

fn time(tok: &[u8]) -> Option<(i64, i64, i64)> {
    let (h, rest) = digits(tok, 1, 2)?;
    let rest = rest.strip_prefix(b":")?;
    let (m, rest) = digits(rest, 1, 2)?;
    let rest = rest.strip_prefix(b":")?;
    let (s, _) = digits(rest, 1, 2)?;
    Some((h, m, s))
}

fn month(tok: &[u8]) -> Option<i64> {
    if tok.len() < 3 {
        return None;
    }
    let head = tok[..3].to_ascii_lowercase();
    MONTHS.iter().position(|m| head[..] == m[..]).map(|i| i as i64 + 1)
}

/// Seconds since the epoch, or `None` when the string is not a cookie-date.
pub fn parse_cookie_date(s: &str) -> Option<i64> {
    let mut found_time = None;
    let mut found_day = None;
    let mut found_month = None;
    let mut found_year = None;

    for tok in s.as_bytes().split(|&b| is_delimiter(b)).filter(|t| !t.is_empty()) {
        if found_time.is_none() {
            if let Some(t) = time(tok) {
                found_time = Some(t);
                continue;
            }
        }
        if found_day.is_none() {
            if let Some((d, _)) = digits(tok, 1, 2) {
                found_day = Some(d);
                continue;
            }
        }
        if found_month.is_none() {
            if let Some(m) = month(tok) {
                found_month = Some(m);
                continue;
            }
        }
        if found_year.is_none() {
            if let Some((y, _)) = digits(tok, 2, 4) {
                found_year = Some(y);
                continue;
            }
        }
    }

    let (hour, minute, second) = found_time?;
    let day = found_day?;
    let month = found_month?;
    let mut year = found_year?;

    if (50..=99).contains(&year) {
        year += 1900;
    } else if (0..=49).contains(&year) {
        year += 2000;
    }

    if !(1..=31).contains(&day) || year < 1601 || hour > 23 || minute > 59 || second > 59 {
        return None;
    }
    timestamp(year, month, day, hour, minute, second)
}
