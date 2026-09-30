//! The cookie store.

mod evict;
mod order;
mod select;
mod store;

use crate::psl::List;

/// A point on the replay clock. `seq` orders events that share a clock
/// value, in transcript order.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Stamp {
    pub time: i64,
    pub seq: u64,
}

#[derive(Clone, Debug)]
pub struct Cookie {
    pub name: String,
    pub value: String,
    pub domain: String,
    pub path: String,
    /// `None` for session cookies.
    pub expiry: Option<i64>,
    pub host_only: bool,
    pub secure: bool,
    pub http_only: bool,
    pub created: Stamp,
    pub accessed: Stamp,
}

impl Cookie {
    pub fn is_expired(&self, now: i64) -> bool {
        matches!(self.expiry, Some(t) if t <= now)
    }
}

pub struct Jar {
    cookies: Vec<Cookie>,
    clock: i64,
    seq: u64,
    psl: List,
}

impl Jar {
    pub fn new(psl: List) -> Jar {
        Jar {
            cookies: Vec::new(),
            clock: 0,
            seq: 0,
            psl,
        }
    }

    pub fn clock(&self) -> i64 {
        self.clock
    }

    pub fn set_clock(&mut self, t: i64) {
        self.clock = t;
    }

    /// Cookies that have not expired at the current clock, in store order.
    pub fn live_cookies(&self) -> impl Iterator<Item = &Cookie> {
        let now = self.clock;
        self.cookies.iter().filter(move |c| !c.is_expired(now))
    }

    fn stamp(&mut self) -> Stamp {
        self.seq += 1;
        Stamp {
            time: self.clock,
            seq: self.seq,
        }
    }
}
