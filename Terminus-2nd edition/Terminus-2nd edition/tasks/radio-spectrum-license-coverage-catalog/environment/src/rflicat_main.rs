use rf_license_atlas::rollup_emit::emit as catalog_emit;
use rf_license_atlas::checkpoint::lineage;
use rf_license_atlas::checkpoint::wal;
use rf_license_atlas::grants;
use rf_license_atlas::catalog_schema::Config;
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
        "prepare-atlas" => run_prepare(&cfg, &args),
        "render-atlas" => run_emit(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/rflicat.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: rflicat prepare-atlas|render-atlas ...");
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

fn run_prepare(cfg: &Config, args: &[String]) -> Result<(), i32> {
    run_compile(cfg, args)?;
    run_coverage(cfg, args)
}

fn run_compile(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (seed, bundle) = parse_seed_bundle(args, 2)?;
    let path = grants::bundle_path(&bundle);
    let bf = grants::load_bundle(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    wal::write_snapshot(&cfg.wal_path, &seed, &bundle, &bf).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_coverage(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (seed, bundle) = parse_seed_bundle(args, 2)?;
    lineage::run_coverage(cfg, &seed, &bundle).map_err(|e| {
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
    let cat = catalog_emit::build_catalog(cfg, &seed, &bundle).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let out = PathBuf::from(output);
    catalog_emit::write_catalog(&out, &cat).map_err(|e| {
        eprintln!("{e}");
        1
    })
}
