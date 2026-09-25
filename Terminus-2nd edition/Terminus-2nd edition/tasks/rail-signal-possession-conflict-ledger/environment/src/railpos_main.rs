use rail_possession_ledger::authority_ticket;
use rail_possession_ledger::scenario_io;
use rail_possession_ledger::topo_persist;
use rail_possession_ledger::rail_model::Config;
use rail_possession_ledger::ledger_emit;
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
        "compile-trackgraph" => run_compile(&cfg, &args),
        "emit-conflicts" => run_emit(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/railpos.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: railpos compile-trackgraph|emit-conflicts ...");
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
    let path = scenario_io::scenario_path(&scenario);
    let sf = scenario_io::load_scenario(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    scenario_io::validate_scenario(&sf, &scenario).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    topo_persist::write_snapshot(&cfg.trackgraph_cache_path, &seed, &scenario, &sf).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    authority_ticket::run_stage(cfg, &seed, &scenario).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_emit(cfg: &Config, args: &[String]) -> Result<(), i32> {
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
    let rep = ledger_emit::build_ledger(cfg, &seed, &scenario).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let out = PathBuf::from(output);
    ledger_emit::write_ledger(&out, &rep).map_err(|e| {
        eprintln!("{e}");
        1
    })
}
