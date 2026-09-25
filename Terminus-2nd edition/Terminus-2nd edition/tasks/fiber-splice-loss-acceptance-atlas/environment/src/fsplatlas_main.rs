use fiber_splice_atlas::types::Config;
use std::env;
use std::fs;
use std::path::PathBuf;

fn load_cfg() -> Config {
    let raw = fs::read_to_string("/app/config/fsplatlas.json").expect("config");
    serde_json::from_str(&raw).expect("config json")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: fsplatlas load-capture|scan-reflections|correlate-span|publish-verdict");
        std::process::exit(2);
    }
    let cfg = load_cfg();
    match args[1].as_str() {
        "load-capture" => cmd_load(&cfg, &args),
        "scan-reflections" => cmd_scan(&cfg, &args),
        "correlate-span" => cmd_correlate(&cfg, &args),
        "publish-verdict" => cmd_publish(&cfg, &args),
        _ => {
            eprintln!("unknown subcommand");
            std::process::exit(2);
        }
    }
}

fn flag(args: &[String], name: &str) -> String {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .cloned()
        .unwrap_or_default()
}

fn cmd_load(cfg: &Config, args: &[String]) {
    let run_id = flag(args, "--run-id");
    let root = fiber_splice_atlas::trace_root();
    let manifest = PathBuf::from(format!("{root}/traces/{run_id}/trace_manifest.json"));
    let plan = PathBuf::from(format!("{root}/plans/{run_id}/splice_plan.json"));
    if let Err(e) = fiber_splice_atlas::bundle_latch::load_capture(&run_id, &manifest, &plan, &cfg.capture_cache_dir) {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

fn cmd_scan(cfg: &Config, args: &[String]) {
    let run_id = flag(args, "--run-id");
    let cache_path = format!("{}/{}.json", cfg.capture_cache_dir, run_id);
    let raw = fs::read_to_string(&cache_path).expect("capture cache");
    let plan: fiber_splice_atlas::types::CaptureCache = serde_json::from_str(&raw).expect("cache json");
    let root = fiber_splice_atlas::trace_root();
    let samples = PathBuf::from(format!("{root}/traces/{run_id}/samples.jsonl"));
    if let Err(e) = fiber_splice_atlas::morlet_scan::scan_reflections(&plan, &samples, &cfg.reflection_buffer_dir) {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

fn cmd_correlate(cfg: &Config, args: &[String]) {
    let run_id = flag(args, "--run-id");
    let cache_path = format!("{}/{}.json", cfg.capture_cache_dir, run_id);
    let raw = fs::read_to_string(&cache_path).expect("capture cache");
    let plan: fiber_splice_atlas::types::CaptureCache = serde_json::from_str(&raw).expect("cache json");
    let events = format!("{}/{}.jsonl", cfg.reflection_buffer_dir, run_id);
    let root = fiber_splice_atlas::trace_root();
    let segments = PathBuf::from(format!("{root}/routes/{run_id}/segments.json"));
    let inventory = PathBuf::from(format!("{}/inventory/connectors.json", cfg.fixture_root));
    if let Err(e) = fiber_splice_atlas::route_weave::correlate_span(
        &plan,
        &events,
        &segments,
        &inventory,
        &cfg.topology_snapshot_dir,
    ) {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

fn cmd_publish(cfg: &Config, args: &[String]) {
    let run_id = flag(args, "--run-id");
    let output = flag(args, "--output");
    let bind_path = format!("{}/{}.json", cfg.topology_snapshot_dir, run_id);
    if let Err(e) = fiber_splice_atlas::atlas_emit::publish_verdict(&run_id, &bind_path, &output) {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
