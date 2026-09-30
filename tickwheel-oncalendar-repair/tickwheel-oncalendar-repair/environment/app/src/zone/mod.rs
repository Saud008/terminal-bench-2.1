//! Time zone support: UTC and TZif files from the system zoneinfo tree.

pub mod rule;
pub mod tzif;

use crate::civil::{gmtime, Tm};
use std::fs;
use std::io::Read;

pub const ZONEINFO_DIR: &str = "/usr/share/zoneinfo";

#[derive(Debug, Clone)]
pub enum Zone {
    Utc,
    Tzif(Box<tzif::TzData>),
}

impl Zone {
    pub fn load(name: &str) -> Option<Zone> {
        let path = format!("{}/{}", ZONEINFO_DIR, name);
        let data = fs::read(path).ok()?;
        tzif::parse(&data).map(|d| Zone::Tzif(Box::new(d)))
    }

    /// Wall time at `t` in this zone, with `isdst` filled in.
    pub fn localtime(&self, t: i64) -> Tm {
        match self {
            Zone::Utc => gmtime(t),
            Zone::Tzif(data) => data.localtime(t),
        }
    }
}

/// Accepts a zone name the way the timer tooling does: a restricted
/// character set, no empty path components, and a regular file under the
/// zoneinfo directory that starts with the TZif magic.
pub fn is_valid_name(name: &str) -> bool {
    if name.is_empty() {
        return false;
    }
    if name == "UTC" {
        return true;
    }
    if name.starts_with('/') {
        return false;
    }

    let mut slash = false;
    for ch in name.chars() {
        let ok = ch.is_ascii_alphanumeric() || matches!(ch, '-' | '_' | '+' | '/');
        if !ok {
            return false;
        }
        if ch == '/' {
            if slash {
                return false;
            }
            slash = true;
        } else {
            slash = false;
        }
    }
    if slash {
        return false;
    }
    if name.len() > 4096 {
        return false;
    }

    let path = format!("{}/{}", ZONEINFO_DIR, name);
    let meta = match fs::metadata(&path) {
        Ok(m) => m,
        Err(_) => return false,
    };
    if !meta.is_file() {
        return false;
    }
    let mut f = match fs::File::open(&path) {
        Ok(f) => f,
        Err(_) => return false,
    };
    let mut magic = [0u8; 4];
    if f.read_exact(&mut magic).is_err() {
        return false;
    }
    &magic == b"TZif"
}
