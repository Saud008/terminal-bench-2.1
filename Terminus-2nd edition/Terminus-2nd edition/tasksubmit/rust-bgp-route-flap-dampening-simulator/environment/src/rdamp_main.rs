use route_damp::atlas_emit;
use route_damp::feed_normalize;
use route_damp::fixture_root;
use route_damp::forecast_emit;
use route_damp::drive_runner;

fn main() {
    if let Err(code) = run() {
        std::process::exit(code);
    }
}

fn run() -> Result<(), i32> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        usage();
        return Err(2);
    }
    match args[1].as_str() {
        "compile-scenario" => parse_scenario(&args, 2, feed_normalize::compile_scenario),
        "drive-feed" => parse_scenario(&args, 2, drive_runner::drive_feed),
        "emit-atlas" => parse_emit(&args, atlas_emit::emit_atlas),
        "emit-reuse-forecast" => parse_emit(&args, forecast_emit::emit_reuse_forecast),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn parse_scenario<F>(args: &[String], start: usize, f: F) -> Result<(), i32>
where
    F: Fn(&str, &str) -> Result<(), String>,
{
    let mut scenario = String::new();
    let mut root = fixture_root();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--scenario" if i + 1 < args.len() => {
                scenario = args[i + 1].clone();
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
    if scenario.is_empty() {
        eprintln!("--scenario required");
        return Err(2);
    }
    f(&scenario, &root).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn parse_emit<F>(args: &[String], f: F) -> Result<(), i32>
where
    F: Fn(&str, &str, &str) -> Result<(), String>,
{
    let mut scenario = String::new();
    let mut out = String::new();
    let mut root = fixture_root();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--scenario" if i + 1 < args.len() => {
                scenario = args[i + 1].clone();
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
    if scenario.is_empty() || out.is_empty() {
        eprintln!("emit needs --scenario and --out");
        return Err(2);
    }
    f(&scenario, &root, &out).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("rdampctl compile-scenario --scenario S [--root D]");
    eprintln!("rdampctl drive-feed --scenario S [--root D]");
    eprintln!("rdampctl emit-atlas --scenario S --out P [--root D]");
    eprintln!("rdampctl emit-reuse-forecast --scenario S --out P [--root D]");
}
