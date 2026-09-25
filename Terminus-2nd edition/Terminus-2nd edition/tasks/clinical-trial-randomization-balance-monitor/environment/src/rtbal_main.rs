use rtbal_monitor::{compile_trial, emit_closure, fixture_root, accept_log, run_balance};

fn main() {
    if let Err(code) = dispatch() {
        std::process::exit(code);
    }
}

fn dispatch() -> Result<(), i32> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        usage();
        return Err(2);
    }
    match args[1].as_str() {
        "compile-trial" => parse_trial(&args, compile_trial::compile_trial),
        "accept-log" => parse_trial(&args, accept_log::accept_log),
        "run-balance" => parse_trial(&args, run_balance::run_balance),
        "emit-closure" => parse_emit(&args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn parse_trial<F>(args: &[String], f: F) -> Result<(), i32>
where
    F: Fn(&str, &str) -> Result<(), String>,
{
    let mut trial = String::new();
    let mut root = fixture_root();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--trial" if i + 1 < args.len() => {
                trial = args[i + 1].clone();
                i += 2;
            }
            "--root" if i + 1 < args.len() => {
                root = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if trial.is_empty() {
        eprintln!("--trial required");
        return Err(2);
    }
    f(&trial, &root).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn parse_emit(args: &[String]) -> Result<(), i32> {
    let mut trial = String::new();
    let mut out = String::new();
    let mut root = fixture_root();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--trial" if i + 1 < args.len() => {
                trial = args[i + 1].clone();
                i += 2;
            }
            "--out" if i + 1 < args.len() => {
                out = args[i + 1].clone();
                i += 2;
            }
            "--root" if i + 1 < args.len() => {
                root = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if trial.is_empty() || out.is_empty() {
        eprintln!("emit-closure needs --trial and --out");
        return Err(2);
    }
    emit_closure::emit_closure(&trial, &root, &out).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("rtbalctl compile-trial --trial T [--root D]");
    eprintln!("rtbalctl accept-log --trial T [--root D]");
    eprintln!("rtbalctl run-balance --trial T [--root D]");
    eprintln!("rtbalctl emit-closure --trial T --out P [--root D]");
}
