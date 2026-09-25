use geo_overlap_curator::ingest_bundle;
use geo_overlap_curator::generation_store;
use geo_overlap_curator::feed_cache_store;
use geo_overlap_curator::types::Config;
use std::fs;
use std::path::PathBuf;

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
    let cfg = load_config()?;
    match args[1].as_str() {
        "compile-feeds" => run_ingest(&cfg, &args),
        "run-reconcile" => run_reconcile(&cfg, &args),
        "emit-overlap" => run_emit(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/geocur.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: geocur compile-feeds|run-reconcile|emit-overlap ...");
}

fn parse_seed_bundle(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut seed = String::new();
    let mut bundle = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].clone();
                i += 2;
            }
            "--bundle" if i + 1 < args.len() => {
                bundle = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if seed.is_empty() || bundle.is_empty() {
        eprintln!("--seed and --bundle required");
        return Err(2);
    }
    Ok((seed, bundle))
}

fn run_ingest(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (seed, bundle) = parse_seed_bundle(args, 2)?;
    let path = ingest_bundle::bundle_path(&bundle);
    let bf = ingest_bundle::load_bundle(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    feed_cache_store::write_snapshot(&cfg.feed_cache_path, &seed, &bundle, &bf).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_reconcile(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (seed, bundle) = parse_seed_bundle(args, 2)?;
    generation_store::run_stage(cfg, &seed, &bundle).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_emit(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let mut seed = String::new();
    let mut bundle = String::new();
    let mut output = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].clone();
                i += 2;
            }
            "--bundle" if i + 1 < args.len() => {
                bundle = args[i + 1].clone();
                i += 2;
            }
            "--output" if i + 1 < args.len() => {
                output = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if seed.is_empty() || bundle.is_empty() || output.is_empty() {
        eprintln!("--seed, --bundle, --output required");
        return Err(2);
    }
    let rep = geo_overlap_curator::emit_report::build_report(cfg, &seed, &bundle).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let out = PathBuf::from(output);
    geo_overlap_curator::emit_report::write_report(&out, &rep).map_err(|e| {
        eprintln!("{e}");
        1
    })
}
