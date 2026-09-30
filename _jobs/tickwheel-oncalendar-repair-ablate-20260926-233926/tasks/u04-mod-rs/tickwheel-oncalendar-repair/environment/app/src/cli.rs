use crate::engine::next_usec;
use crate::errno::Errno;
use crate::spec;
use crate::table::Table;
use crate::timestamp::{format_utc, parse_base_time};
use std::io::Write;
use std::time::{SystemTime, UNIX_EPOCH};

const USAGE: &str = "usage: tickwheel calendar [--base-time=TIME] [--iterations=N] EXPRESSION...\n";

struct Options {
    base: Option<u64>,
    iterations: u32,
    exprs: Vec<String>,
}

fn parse_args(args: &[String]) -> Result<Options, String> {
    let mut it = args.iter();
    match it.next().map(String::as_str) {
        Some("calendar") => {}
        Some(other) => return Err(format!("unknown command '{}'", other)),
        None => return Err("missing command".to_string()),
    }

    let mut opts = Options { base: None, iterations: 1, exprs: Vec::new() };
    let mut only_exprs = false;
    while let Some(a) = it.next() {
        if only_exprs || !a.starts_with("--") {
            opts.exprs.push(a.clone());
            continue;
        }
        if a == "--" {
            only_exprs = true;
            continue;
        }
        let (name, inline) = match a.split_once('=') {
            Some((n, v)) => (n, Some(v.to_string())),
            None => (a.as_str(), None),
        };
        let mut value = || -> Result<String, String> {
            match &inline {
                Some(v) => Ok(v.clone()),
                None => it.next().cloned().ok_or_else(|| format!("option '{}' needs a value", name)),
            }
        };
        match name {
            "--base-time" => {
                let v = value()?;
                opts.base = Some(parse_base_time(&v).ok_or_else(|| format!("failed to parse --base-time: {}", v))?);
            }
            "--iterations" => {
                let v = value()?;
                opts.iterations = v.parse().map_err(|_| format!("failed to parse --iterations: {}", v))?;
            }
            _ => return Err(format!("unknown option '{}'", name)),
        }
    }
    if opts.exprs.is_empty() {
        return Err("calendar needs at least one expression".to_string());
    }
    Ok(opts)
}

fn report(expr: &str, base: u64, iterations: u32) -> Result<String, String> {
    let spec = spec::parse(expr)
        .map_err(|e| format!("Failed to parse calendar specification '{}': {}", expr, e))?;

    let normalized = spec.to_normalized_string();
    let mut table = Table::new();
    if normalized != expr {
        table.add("Original form:", expr);
    }
    table.add("Normalized form:", &normalized);

    let mut n = base;
    for i in 0..iterations {
        match next_usec(&spec, n) {
            Err(Errno::NoEnt) => {
                if i == 0 {
                    table.add("Next elapse:", "never");
                }
                break;
            }
            Err(e) => {
                return Err(format!("Failed to determine next elapse for '{}': {}", expr, e));
            }
            Ok(next) => {
                let label = if i == 0 { "Next elapse:".to_string() } else { format!("Iter. #{}:", i + 1) };
                table.add(&label, &format_utc(next));
                n = next;
            }
        }
    }
    Ok(table.render())
}

pub fn run(args: &[String]) -> i32 {
    if args.iter().any(|a| a == "--help" || a == "-h") {
        print!("{}", USAGE);
        return 0;
    }

    let opts = match parse_args(args) {
        Ok(o) => o,
        Err(msg) => {
            eprintln!("tickwheel: {}", msg);
            eprint!("{}", USAGE);
            return 2;
        }
    };

    let base = opts.base.unwrap_or_else(|| {
        SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_micros() as u64).unwrap_or(0)
    });

    let stdout = std::io::stdout();
    let mut out = stdout.lock();
    let mut status = 0;
    for (i, expr) in opts.exprs.iter().enumerate() {
        match report(expr, base, opts.iterations) {
            Ok(text) => {
                let _ = out.write_all(text.as_bytes());
            }
            Err(msg) => {
                let _ = out.flush();
                eprintln!("{}", msg);
                status = 1;
            }
        }
        if i + 1 < opts.exprs.len() {
            let _ = out.write_all(b"\n");
        }
    }
    let _ = out.flush();
    status
}
