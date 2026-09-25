use seismocomply::atlas_emit;
use seismocomply::passport;
use seismocomply::run_buffer;
use seismocomply::seismo_peak;
use seismocomply::types::Config;
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
        "load-survey" => run_load_survey(&cfg, &args),
        "correlate" => run_correlate(&cfg, &args),
        "publish-atlas" => run_publish_atlas(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/seismocomply.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: seismocomply load-survey|correlate|publish-atlas ...");
}

fn parse_seed_survey(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut seed = String::new();
    let mut survey = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].clone();
                i += 2;
            }
            "--survey" if i + 1 < args.len() => {
                survey = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if seed.is_empty() || survey.is_empty() {
        eprintln!("--seed and --survey required");
        return Err(2);
    }
    Ok((seed, survey))
}

fn run_load_survey(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (seed, survey) = parse_seed_survey(args, 2)?;
    let path = seismo_peak::survey_path(&survey);
    let record = seismo_peak::load_survey(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    run_buffer::write_buffer(&cfg.buffer_path, &seed, &record).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_correlate(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (seed, survey) = parse_seed_survey(args, 2)?;
    passport::run_correlate(cfg, &seed, &survey).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_publish_atlas(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let mut seed = String::new();
    let mut survey = String::new();
    let mut output = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].clone();
                i += 2;
            }
            "--survey" if i + 1 < args.len() => {
                survey = args[i + 1].clone();
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
    if seed.is_empty() || survey.is_empty() || output.is_empty() {
        eprintln!("--seed, --survey, --output required");
        return Err(2);
    }
    let atlas = atlas_emit::build_atlas(cfg, &seed, &survey).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let out = PathBuf::from(output);
    atlas_emit::write_atlas(&out, &atlas).map_err(|e| {
        eprintln!("{e}");
        1
    })
}
