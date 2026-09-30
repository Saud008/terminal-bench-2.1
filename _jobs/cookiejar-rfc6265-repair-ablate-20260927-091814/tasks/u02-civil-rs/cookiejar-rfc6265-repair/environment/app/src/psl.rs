//! Public suffix lookups against the vendored list in data/public_suffix.dat.

use crate::host::is_ip_address;
use std::collections::HashSet;

const BUILTIN: &str = include_str!("../data/public_suffix.dat");

pub struct List {
    suffixes: HashSet<String>,
}

impl List {
    pub fn builtin() -> List {
        let suffixes = BUILTIN
            .lines()
            .map(str::trim)
            .filter(|l| !l.is_empty() && !l.starts_with("//"))
            .map(|l| l.to_ascii_lowercase())
            .collect();
        List { suffixes }
    }

    pub fn is_public_suffix(&self, domain: &str) -> bool {
        self.suffixes.contains(domain)
    }

    /// The "site" a host belongs to: its longest listed public suffix plus
    /// one more label. See docs/POLICY.md.
    pub fn registrable_domain(&self, host: &str) -> String {
        if is_ip_address(host) || self.is_public_suffix(host) {
            return host.to_string();
        }
        let labels: Vec<&str> = host.split('.').collect();
        for i in 1..labels.len() {
            if self.is_public_suffix(&labels[i..].join(".")) {
                return labels[i - 1..].join(".");
            }
        }
        if labels.len() > 2 {
            labels[labels.len() - 2..].join(".")
        } else {
            host.to_string()
        }
    }
}
