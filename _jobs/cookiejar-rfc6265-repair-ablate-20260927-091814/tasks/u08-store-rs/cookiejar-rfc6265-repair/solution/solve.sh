#!/usr/bin/env bash
set -euo pipefail

cd /app

cat > src/host.rs <<'CJ_SRC_HOST_RS'
/// True for a dotted-quad IPv4 address such as `192.0.2.7`.
pub fn is_ip_address(host: &str) -> bool {
    let parts: Vec<&str> = host.split('.').collect();
    parts.len() == 4
        && parts.iter().all(|p| {
            !p.is_empty()
                && p.len() <= 3
                && p.bytes().all(|b| b.is_ascii_digit())
                && p.parse::<u16>().map_or(false, |v| v <= 255)
        })
}

/// Domain matching (RFC 6265 section 5.1.3). Both arguments must already be
/// canonicalized.
pub fn domain_match(string: &str, domain: &str) -> bool {
    if string == domain {
        return true;
    }
    string.len() > domain.len()
        && string.ends_with(domain)
        && string.as_bytes()[string.len() - domain.len() - 1] == b'.'
        && !is_ip_address(string)
}
CJ_SRC_HOST_RS

cat > src/time/civil.rs <<'CJ_SRC_TIME_CIVIL_RS'
//! Proleptic Gregorian calendar arithmetic, all in UTC.

pub const SECS_PER_DAY: i64 = 86_400;

pub fn is_leap(year: i64) -> bool {
    year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)
}

pub fn days_in_month(year: i64, month: i64) -> i64 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if is_leap(year) => 29,
        2 => 28,
        _ => 0,
    }
}

/// Days since 1970-01-01.
pub fn days_from_civil(year: i64, month: i64, day: i64) -> i64 {
    let y = if month <= 2 { year - 1 } else { year };
    let era = y.div_euclid(400);
    let yoe = y - era * 400;
    let mp = (month + 9) % 12;
    let doy = (153 * mp + 2) / 5 + day - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + doe - 719_468
}

/// Seconds since the epoch for a calendar date and time of day, or `None`
/// when no such date exists.
pub fn timestamp(year: i64, month: i64, day: i64, hour: i64, minute: i64, second: i64) -> Option<i64> {
    if !(1..=12).contains(&month) || day < 1 || day > days_in_month(year, month) {
        return None;
    }
    Some(days_from_civil(year, month, day) * SECS_PER_DAY + hour * 3600 + minute * 60 + second)
}
CJ_SRC_TIME_CIVIL_RS

cat > src/time/date.rs <<'CJ_SRC_TIME_DATE_RS'
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

    if (70..=99).contains(&year) {
        year += 1900;
    } else if (0..=69).contains(&year) {
        year += 2000;
    }

    if !(1..=31).contains(&day) || year < 1601 || hour > 23 || minute > 59 || second > 59 {
        return None;
    }
    timestamp(year, month, day, hour, minute, second)
}
CJ_SRC_TIME_DATE_RS

cat > src/cookie/parse.rs <<'CJ_SRC_COOKIE_PARSE_RS'
//! Set-Cookie parsing (RFC 6265 section 5.2).

use super::path::default_path;
use crate::time::{date, EARLIEST, LATEST};
use crate::url::Url;

/// One entry of the cookie-attribute-list, already interpreted.
#[derive(Clone, Debug)]
pub enum Attr {
    Expires(i64),
    MaxAge(i64),
    Domain(String),
    Path(String),
    Secure,
    HttpOnly,
}

#[derive(Debug)]
pub struct SetCookie {
    pub name: String,
    pub value: String,
    pub attrs: Vec<Attr>,
}

fn trim_wsp(s: &str) -> &str {
    s.trim_matches(|c| c == ' ' || c == '\t')
}

/// Max-Age attribute value to an expiry-time, relative to `now`.
fn max_age(v: &str, now: i64) -> Option<i64> {
    let (neg, digits) = match v.strip_prefix('-') {
        Some(rest) => (true, rest),
        None => (false, v),
    };
    if digits.is_empty() || !digits.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }
    let delta = digits
        .bytes()
        .fold(0i64, |acc, b| acc.saturating_mul(10).saturating_add(i64::from(b - b'0')));
    if neg || delta == 0 {
        Some(EARLIEST)
    } else {
        Some(now.saturating_add(delta).min(LATEST))
    }
}

/// Parses a set-cookie-string received in a response to `url` at time `now`.
/// Returns `None` when the whole header has to be ignored.
pub fn parse(header: &str, url: &Url, now: i64) -> Option<SetCookie> {
    let (pair, unparsed) = match header.split_once(';') {
        Some((p, rest)) => (p, Some(rest)),
        None => (header, None),
    };

    let (name, value) = pair.split_once('=')?;
    let (name, value) = (trim_wsp(name), trim_wsp(value));
    if name.is_empty() {
        return None;
    }

    let mut attrs = Vec::new();
    for av in unparsed.into_iter().flat_map(|u| u.split(';')) {
        let (n, v) = av.split_once('=').unwrap_or((av, ""));
        let (n, v) = (trim_wsp(n), trim_wsp(v));
        match n.to_ascii_lowercase().as_str() {
            "expires" => {
                if let Some(t) = date::parse_cookie_date(v) {
                    attrs.push(Attr::Expires(t.clamp(EARLIEST, LATEST)));
                }
            }
            "max-age" => {
                if let Some(t) = max_age(v, now) {
                    attrs.push(Attr::MaxAge(t));
                }
            }
            "domain" => {
                if !v.is_empty() {
                    let d = v.strip_prefix('.').unwrap_or(v);
                    attrs.push(Attr::Domain(d.to_ascii_lowercase()));
                }
            }
            "path" => {
                let p = if v.starts_with('/') { v.to_string() } else { default_path(&url.path) };
                attrs.push(Attr::Path(p));
            }
            "secure" => attrs.push(Attr::Secure),
            "httponly" => attrs.push(Attr::HttpOnly),
            _ => {}
        }
    }

    Some(SetCookie {
        name: name.to_string(),
        value: value.to_string(),
        attrs,
    })
}
CJ_SRC_COOKIE_PARSE_RS

cat > src/cookie/path.rs <<'CJ_SRC_COOKIE_PATH_RS'
//! Paths and path-match (RFC 6265 section 5.1.4).

/// The default-path of a request-uri path.
pub fn default_path(uri_path: &str) -> String {
    if !uri_path.starts_with('/') {
        return "/".to_string();
    }
    match uri_path.rfind('/') {
        Some(0) | None => "/".to_string(),
        Some(i) => uri_path[..i].to_string(),
    }
}

pub fn path_match(request_path: &str, cookie_path: &str) -> bool {
    if request_path == cookie_path {
        return true;
    }
    request_path.starts_with(cookie_path)
        && (cookie_path.ends_with('/') || request_path.as_bytes()[cookie_path.len()] == b'/')
}
CJ_SRC_COOKIE_PATH_RS

cat > src/cookie/domain.rs <<'CJ_SRC_COOKIE_DOMAIN_RS'
//! Which hosts a new cookie is scoped to (RFC 6265 section 5.3, steps 4-6).

use super::parse::Attr;
use crate::host::domain_match;
use crate::psl::List;

pub enum Scope {
    /// Only sent back to exactly this host.
    HostOnly(String),
    /// Sent to this domain and every subdomain of it.
    Domain(String),
}

/// `None` means the cookie must be ignored.
pub fn resolve(attrs: &[Attr], host: &str, psl: &List) -> Option<Scope> {
    let mut domain = attrs
        .iter()
        .rev()
        .find_map(|a| match a {
            Attr::Domain(d) => Some(d.clone()),
            _ => None,
        })
        .unwrap_or_default();

    if !domain.is_empty() && psl.is_public_suffix(&domain) {
        if domain == host {
            domain.clear();
        } else {
            return None;
        }
    }

    if domain.is_empty() {
        return Some(Scope::HostOnly(host.to_string()));
    }
    if !domain_match(host, &domain) {
        return None;
    }
    Some(Scope::Domain(domain))
}
CJ_SRC_COOKIE_DOMAIN_RS

cat > src/cookie/expiry.rs <<'CJ_SRC_COOKIE_EXPIRY_RS'
use super::parse::Attr;

pub enum Lifetime {
    Session,
    Persistent(i64),
}

/// Lifetime of a new cookie from its attribute list (RFC 6265 section 5.3,
/// step 3).
pub fn resolve(attrs: &[Attr]) -> Lifetime {
    let last_max_age = attrs.iter().rev().find_map(|a| match a {
        Attr::MaxAge(t) => Some(*t),
        _ => None,
    });
    let last_expires = attrs.iter().rev().find_map(|a| match a {
        Attr::Expires(t) => Some(*t),
        _ => None,
    });
    last_max_age
        .or(last_expires)
        .map_or(Lifetime::Session, Lifetime::Persistent)
}
CJ_SRC_COOKIE_EXPIRY_RS


cat > src/jar/select.rs <<'CJ_SRC_JAR_SELECT_RS'
//! Building the Cookie header (RFC 6265 section 5.4).

use super::{order, Cookie, Jar};
use crate::cookie::path::path_match;
use crate::host::domain_match;
use crate::url::Url;

fn applies_to(c: &Cookie, url: &Url) -> bool {
    let domain_ok = if c.host_only {
        url.host == c.domain
    } else {
        domain_match(&url.host, &c.domain)
    };
    domain_ok && path_match(&url.path, &c.path) && (!c.secure || url.secure)
}

impl Jar {
    /// The Cookie header value for an HTTP request to `url` (empty when no
    /// cookie applies). Updates the last-access-time of every cookie sent.
    pub fn cookie_header(&mut self, url: &Url) -> String {
        self.purge_expired();
        let stamp = self.stamp();

        let mut hits: Vec<usize> = (0..self.cookies.len())
            .filter(|&i| applies_to(&self.cookies[i], url))
            .collect();
        order::sort(&mut hits, &self.cookies);

        let mut parts = Vec::with_capacity(hits.len());
        for &i in &hits {
            let c = &mut self.cookies[i];
            c.accessed = stamp;
            parts.push(format!("{}={}", c.name, c.value));
        }
        parts.join("; ")
    }
}
CJ_SRC_JAR_SELECT_RS

cat > src/jar/order.rs <<'CJ_SRC_JAR_ORDER_RS'
use super::Cookie;

/// Orders the indices of the cookies going into one Cookie header.
pub fn sort(hits: &mut [usize], cookies: &[Cookie]) {
    hits.sort_by(|&a, &b| {
        let (a, b) = (&cookies[a], &cookies[b]);
        b.path.len().cmp(&a.path.len()).then_with(|| a.created.cmp(&b.created))
    });
}
CJ_SRC_JAR_ORDER_RS

cat > src/jar/evict.rs <<'CJ_SRC_JAR_EVICT_RS'
//! Removing cookies: expiry, and the per-site limit from docs/POLICY.md.

use super::Jar;

pub const MAX_COOKIES_PER_SITE: usize = 6;

impl Jar {
    pub(super) fn purge_expired(&mut self) {
        let now = self.clock;
        self.cookies.retain(|c| !c.is_expired(now));
    }

    /// Evicts cookies of `site` until it is back within the limit.
    pub(super) fn enforce_site_limit(&mut self, site: &str) {
        loop {
            let members: Vec<usize> = (0..self.cookies.len())
                .filter(|&i| self.psl.registrable_domain(&self.cookies[i].domain) == site)
                .collect();
            if members.len() <= MAX_COOKIES_PER_SITE {
                return;
            }
            let victim = members
                .into_iter()
                .min_by_key(|&i| (self.cookies[i].accessed, self.cookies[i].created))
                .expect("site has members");
            self.cookies.remove(victim);
        }
    }
}
CJ_SRC_JAR_EVICT_RS

cargo build --release --offline
crumbjar replay examples/basic.txt
crumbjar replay examples/subdomains.txt
crumbjar replay examples/expiry.txt
