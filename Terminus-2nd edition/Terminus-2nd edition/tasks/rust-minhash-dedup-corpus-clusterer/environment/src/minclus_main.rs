use minhash_corpus_clusterer::attest_report;
use minhash_corpus_clusterer::graph_build;
use minhash_corpus_clusterer::sketch_write;
use minhash_corpus_clusterer::types::Config;
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
        "scan" | "ingest" => run_scan(&cfg, &args),
        "group" => run_group(&cfg, &args),
        "attest" | "export" => run_attest(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/minclus.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: minclus scan|group|attest ...");
}

fn run_scan(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let mut corpus_dir = String::new();
    let mut run_id = String::new();
    let mut profile = String::from("default");
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--corpus-dir" if i + 1 < args.len() => {
                corpus_dir = args[i + 1].clone();
                i += 2;
            }
            "--run-id" if i + 1 < args.len() => {
                run_id = args[i + 1].clone();
                i += 2;
            }
            "--profile" if i + 1 < args.len() => {
                profile = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if corpus_dir.is_empty() || run_id.is_empty() {
        eprintln!("--corpus-dir and --run-id required");
        return Err(2);
    }
    let salt = minhash_corpus_clusterer::perm_salt();
    sketch_write::scan_corpus(
        cfg,
        &PathBuf::from(corpus_dir),
        &run_id,
        &profile,
        &salt,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn run_group(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let mut run_id = String::new();
    let mut floor = cfg.default_jaccard_floor;
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--run-id" if i + 1 < args.len() => {
                run_id = args[i + 1].clone();
                i += 2;
            }
            "--jaccard-floor" if i + 1 < args.len() => {
                floor = args[i + 1].parse().map_err(|_| 2)?;
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if run_id.is_empty() {
        eprintln!("--run-id required");
        return Err(2);
    }
    graph_build::build_graph(cfg, &run_id, floor).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn run_attest(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let mut run_id = String::new();
    let mut output = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--run-id" if i + 1 < args.len() => {
                run_id = args[i + 1].clone();
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
    if run_id.is_empty() || output.is_empty() {
        eprintln!("--run-id and --output required");
        return Err(2);
    }
    attest_report::write_report(cfg, &run_id, &PathBuf::from(output)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
