use substation_interlock::loto_ticket;
use substation_interlock::scenario_loader;
use substation_interlock::diag_emit;
use substation_interlock::yard_model::Config;
use substation_interlock::seq_anchor;
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
        "compile-yard" => run_compile(&cfg, &args),
        "verify-order" => run_verify(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/sublock.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: relayctl compile-yard|verify-order ...");
}

fn parse_seed_scenario(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut seed = String::new();
    let mut scenario = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].clone();
                i += 2;
            }
            "--scenario" if i + 1 < args.len() => {
                scenario = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if seed.is_empty() || scenario.is_empty() {
        eprintln!("--seed and --scenario required");
        return Err(2);
    }
    Ok((seed, scenario))
}

fn run_compile(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (seed, scenario) = parse_seed_scenario(args, 2)?;
    let path = scenario_loader::scenario_path(&scenario);
    let sf = scenario_loader::load_scenario(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    scenario_loader::validate_scenario(&sf, &scenario).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    seq_anchor::write_snapshot(&cfg.yard_cache_path, &seed, &scenario, &sf).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    loto_ticket::run_stage(cfg, &seed, &scenario).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_verify(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let mut seed = String::new();
    let mut scenario = String::new();
    let mut output = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].clone();
                i += 2;
            }
            "--scenario" if i + 1 < args.len() => {
                scenario = args[i + 1].clone();
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
    if seed.is_empty() || scenario.is_empty() || output.is_empty() {
        eprintln!("--seed, --scenario, --output required");
        return Err(2);
    }
    let snap = seq_anchor::read_snapshot(&cfg.yard_cache_path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    seq_anchor::validate_seed_scenario(&snap, &seed, &scenario).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let ticket = loto_ticket::read_ticket(&cfg.loto_ticket_path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    loto_ticket::validate_ticket(&ticket, &snap).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let sf = scenario_loader::load_scenario(&scenario_loader::scenario_path(&scenario)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let rep = diag_emit::build_report(&snap, &sf, &ticket, &seed, &scenario);
    diag_emit::write_report(&PathBuf::from(output), &rep).map_err(|e| {
        eprintln!("{e}");
        1
    })
}
