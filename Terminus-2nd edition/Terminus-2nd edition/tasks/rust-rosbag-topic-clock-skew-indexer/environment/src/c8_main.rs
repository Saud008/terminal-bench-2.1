use rosbag_skew_indexer::peskin_pq;
use rosbag_skew_indexer::kennel_io;
use rosbag_skew_indexer::hopf_weave;
use rosbag_skew_indexer::ruelle_pq;
use rosbag_skew_indexer::types::Config;
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
        "latch-meta" => latch_manifest(&cfg, &args),
        "norm-stream" => norm_stream(&cfg, &args),
        "match-sync" => match_sync(&cfg, &args),
        "emit-skew" => emit_skew(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/skew-cal.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: skew-cal latch-meta|norm-stream|match-sync|emit-skew ...");
}

fn bag_id_arg(args: &[String]) -> Result<String, i32> {
    let mut bag_id = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--bag-id" && i + 1 < args.len() {
            bag_id = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if bag_id.is_empty() {
        eprintln!("--bag-id required");
        return Err(2);
    }
    Ok(bag_id)
}

fn latch_manifest(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let bag_id = bag_id_arg(args)?;
    let mut meta_path = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--meta" && i + 1 < args.len() {
            meta_path = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if meta_path.is_empty() {
        eprintln!("--meta required");
        return Err(2);
    }
    kennel_io::latch_manifest(&bag_id, &PathBuf::from(meta_path), &cfg.manifest_latch_dir).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn load_meta(cfg: &Config, bag_id: &str) -> Result<rosbag_skew_indexer::types::ManifestLatch, i32> {
    let path = format!("{}/{}.json", cfg.manifest_latch_dir, bag_id);
    let raw = fs::read_to_string(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn norm_stream(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let bag_id = bag_id_arg(args)?;
    let meta = load_meta(cfg, &bag_id)?;
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
    hopf_weave::norm_stream(&meta, &PathBuf::from(stream), &cfg.timeline_ledger_dir).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn match_sync_cmd(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let bag_id = bag_id_arg(args)?;
    let meta = load_meta(cfg, &bag_id)?;
    let msg_path = format!("{}/{}.jsonl", cfg.timeline_ledger_dir, bag_id);
    ruelle_pq::match_sync(&meta, &msg_path, &cfg.sync_lattice_dir).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn match_sync(cfg: &Config, args: &[String]) -> Result<(), i32> {
    match_sync_cmd(cfg, args)
}

fn emit_skew(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let bag_id = bag_id_arg(args)?;
    let meta = load_meta(cfg, &bag_id)?;
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
    let msg_path = format!("{}/{}.jsonl", cfg.timeline_ledger_dir, bag_id);
    let sync_path = format!("{}/{}.jsonl", cfg.sync_lattice_dir, bag_id);
    peskin_pq::write_atlas(cfg, &meta, &msg_path, &sync_path, &PathBuf::from(output)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
