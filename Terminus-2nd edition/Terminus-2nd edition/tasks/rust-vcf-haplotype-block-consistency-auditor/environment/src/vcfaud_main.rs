use vcf_haplotype_auditor::anomaly_report;
use vcf_haplotype_auditor::edge_wire;
use vcf_haplotype_auditor::sample_matrix;
use vcf_haplotype_auditor::types::Config;
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
        "materialize" => run_materialize(&cfg, &args),
        "wire-blocks" => run_wire_blocks(&cfg, &args),
        "score-anomalies" => run_score_anomalies(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/vcfaud.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: vcfaud materialize|wire-blocks|score-anomalies ...");
}

fn run_materialize(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let mut run_id = String::new();
    let mut vcf = String::new();
    let mut manifest = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--run-id" if i + 1 < args.len() => {
                run_id = args[i + 1].clone();
                i += 2;
            }
            "--vcf" if i + 1 < args.len() => {
                vcf = args[i + 1].clone();
                i += 2;
            }
            "--manifest" if i + 1 < args.len() => {
                manifest = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if run_id.is_empty() || vcf.is_empty() || manifest.is_empty() {
        eprintln!("--run-id --vcf --manifest required");
        return Err(2);
    }
    sample_matrix::materialize_run(cfg, &run_id, &PathBuf::from(vcf), &PathBuf::from(manifest)).map_err(
        |e| {
            eprintln!("{e}");
            1
        },
    )?;
    Ok(())
}

fn run_wire_blocks(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let mut run_id = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--run-id" && i + 1 < args.len() {
            run_id = args[i + 1].clone();
            i += 2;
        } else {
            usage();
            return Err(2);
        }
    }
    if run_id.is_empty() {
        eprintln!("--run-id required");
        return Err(2);
    }
    edge_wire::wire_blocks(cfg, &run_id).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn run_score_anomalies(cfg: &Config, args: &[String]) -> Result<(), i32> {
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
    anomaly_report::write_report(cfg, &run_id, &PathBuf::from(output)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
