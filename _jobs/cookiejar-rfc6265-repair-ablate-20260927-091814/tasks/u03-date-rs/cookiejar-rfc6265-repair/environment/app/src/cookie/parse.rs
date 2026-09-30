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

    let (name, value) = match pair.split_once('=') {
        Some((n, v)) => (trim_wsp(n), trim_wsp(v)),
        None => ("", trim_wsp(pair)),
    };
    if name.is_empty() && value.is_empty() {
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
