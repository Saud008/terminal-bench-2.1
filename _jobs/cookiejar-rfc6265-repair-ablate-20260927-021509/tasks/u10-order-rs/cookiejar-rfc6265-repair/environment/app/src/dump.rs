//! The `dump` listing. Format in docs/cli.md.

use crate::jar::{Cookie, Jar};
use std::io::{self, Write};

fn flags(c: &Cookie) -> String {
    let mut f = Vec::new();
    if c.host_only {
        f.push("host-only");
    }
    if c.secure {
        f.push("secure");
    }
    if c.http_only {
        f.push("httponly");
    }
    if f.is_empty() {
        "-".to_string()
    } else {
        f.join(",")
    }
}

pub fn write<W: Write>(out: &mut W, jar: &Jar) -> io::Result<()> {
    let mut live: Vec<&Cookie> = jar.live_cookies().collect();
    live.sort_by(|a, b| (&a.domain, &a.path, &a.name).cmp(&(&b.domain, &b.path, &b.name)));

    writeln!(out, "-- jar @{}: {} cookie(s)", jar.clock(), live.len())?;
    for c in live {
        let expiry = c.expiry.map_or_else(|| "session".to_string(), |t| t.to_string());
        writeln!(
            out,
            "{}\t{}\t{}={}\t{}\t{}\t{}\t{}",
            c.domain,
            c.path,
            c.name,
            c.value,
            flags(c),
            expiry,
            c.created.time,
            c.accessed.time
        )?;
    }
    Ok(())
}
