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
                .min_by_key(|&i| self.cookies[i].created)
                .expect("site has members");
            self.cookies.remove(victim);
        }
    }
}
