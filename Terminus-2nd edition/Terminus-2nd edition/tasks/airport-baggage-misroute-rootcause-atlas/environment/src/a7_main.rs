use baggage_misroute_atlas::ingress_normalizer;
use baggage_misroute_atlas::output_facet;
use baggage_misroute_atlas::types::Config;
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
        "hub-latch" => hub_latch(&cfg, &args),
        "seq-scans" => seq_scans(&cfg, &args),
        "route-belts" => route_belts(&cfg, &args),
        "emit-rootcause" => emit_rootcause(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/bag-atlas.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: bag-atlas hub-latch|seq-scans|route-belts|emit-rootcause ...");
}

fn hub_id_arg(args: &[String]) -> Result<String, i32> {
    let mut hub_id = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--hub-id" && i + 1 < args.len() {
            hub_id = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if hub_id.is_empty() {
        eprintln!("--hub-id required");
        return Err(2);
    }
    Ok(hub_id)
}

fn hub_latch(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let hub_id = hub_id_arg(args)?;
    let mut topo = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--topology" && i + 1 < args.len() {
            topo = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if topo.is_empty() {
        eprintln!("--topology required");
        return Err(2);
    }
    ingress_normalizer::latch_hub(&hub_id, &PathBuf::from(topo), &cfg.hub_latch_dir).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn load_hub(cfg: &Config, hub_id: &str) -> Result<baggage_misroute_atlas::types::HubLatch, i32> {
    let path = format!("{}/{}.json", cfg.hub_latch_dir, hub_id);
    let raw = fs::read_to_string(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn seq_scans(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let hub_id = hub_id_arg(args)?;
    let hub = load_hub(cfg, &hub_id)?;
    let mut stream = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--stream" && i + 1 < args.len() {
            stream = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if stream.is_empty() {
        eprintln!("--stream required");
        return Err(2);
    }
    ingress_normalizer::seq_scans(&hub, &PathBuf::from(stream), &cfg.scan_ledger_dir).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn route_belts(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let hub_id = hub_id_arg(args)?;
    let hub = load_hub(cfg, &hub_id)?;
    let ledger = format!("{}/{}.jsonl", cfg.scan_ledger_dir, hub_id);
    output_facet::route_belts(&hub, &ledger, &cfg.route_lattice_dir).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn emit_rootcause(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let hub_id = hub_id_arg(args)?;
    let hub = load_hub(cfg, &hub_id)?;
    let mut output = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--output" && i + 1 < args.len() {
            output = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if output.is_empty() {
        eprintln!("--output required");
        return Err(2);
    }
    let lattice = format!("{}/{}.jsonl", cfg.route_lattice_dir, hub_id);
    output_facet::write_atlas(cfg, &hub, &lattice, &PathBuf::from(output)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
