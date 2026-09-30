//! Transcript reader. See docs/transcript.md for the format.

use crate::error::LineError;
use crate::url::Url;

pub enum Command {
    At(i64),
    Set(Url, String),
    Get(Url),
    Dump,
}

pub fn parse(text: &str) -> Result<Vec<Command>, LineError> {
    let mut out = Vec::new();
    let mut clock: i64 = 0;

    for (idx, raw) in text.lines().enumerate() {
        let line_no = idx + 1;
        let err = |msg: String| LineError { line: line_no, msg };

        let line = raw.trim_start();
        if line.trim_end().is_empty() || line.starts_with('#') {
            continue;
        }
        let (word, rest) = line.split_once(' ').unwrap_or((line.trim_end(), ""));

        match word {
            "at" => {
                let v = rest.trim();
                let t: i64 = v.parse().map_err(|_| err(format!("bad clock value {v:?}")))?;
                if t < clock {
                    return Err(err(format!("clock moves backwards ({t} < {clock})")));
                }
                clock = t;
                out.push(Command::At(t));
            }
            "set" => {
                let (u, header) = rest
                    .split_once(' ')
                    .ok_or_else(|| err("set needs a URL and a Set-Cookie value".to_string()))?;
                out.push(Command::Set(Url::parse(u).map_err(err)?, header.to_string()));
            }
            "get" => out.push(Command::Get(Url::parse(rest.trim()).map_err(err)?)),
            "dump" if rest.trim().is_empty() => out.push(Command::Dump),
            _ => return Err(err(format!("unknown command {word:?}"))),
        }
    }
    Ok(out)
}
