use lab_calibration_chain::line_validity;
use lab_calibration_chain::chain_schema::{
    ChannelDecision, Config, RunPack, StagedInstrument,
};
use lab_calibration_chain::row_publish;
use lab_calibration_chain::meter_parse;
use lab_calibration_chain::register_store;
use lab_calibration_chain::run_io;
use lab_calibration_chain::walk_parent;
use lab_calibration_chain::gate_operator;
use lab_calibration_chain::matrix_limits;
use lab_calibration_chain::budget_rss;
use lab_calibration_chain::vault_snapshot;
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
        "ingest" => run_ingest(&cfg, &args),
        "fuse" => run_fuse(&cfg, &args),
        "export" => run_export(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/calbind.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: calbind ingest|fuse|export ...");
}

fn run_ingest(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (batch_id, pack) = parse_batch_pack(args, 2)?;
    let path = run_io::pack_path(&pack);
    let pack_data = run_io::load_pack(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let staged = stage_instrument(cfg, &pack_data).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    vault_snapshot::upsert_batch(
        &cfg.vault_path,
        &batch_id,
        &pack,
        &pack_data.as_of_date,
        staged,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_fuse(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let batch_id = parse_batch(args, 2)?;
    let vault = vault_snapshot::read_vault(&cfg.vault_path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let snap = vault.get(&batch_id).ok_or_else(|| {
        eprintln!("missing vault batch {batch_id}");
        1
    })?;
    let prev = register_store::read_generation(&cfg.register_path, &batch_id);
    register_store::upsert_row(
        &cfg.register_path,
        &batch_id,
        &snap.pack,
        prev,
        &snap.instrument,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn run_export(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (batch_id, output) = parse_batch_output(args, 2)?;
    let report = row_publish::build_dossier(&cfg.register_path, &batch_id).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    row_publish::write_dossier(&PathBuf::from(output), &report).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn stage_instrument(cfg: &Config, pack: &RunPack) -> Result<StagedInstrument, String> {
    let readings = meter_parse::normalize_readings(&pack.readings);
    let cert_valid = line_validity::cert_valid_on_date(&pack.certificate.expires, &pack.as_of_date);
    let digest = line_validity::cert_digest(
        &pack.instrument_id,
        &pack.as_of_date,
        &pack.certificate.cert_id,
    );
    let std_root = walk_parent::trace_root(&pack.standard_chain)?;
    if !walk_parent::chain_complete(&pack.standard_chain) {
        return Err("incomplete standard chain".into());
    }
    let combined = budget_rss::combined_standard(&pack.uncertainty_budget);
    let expanded = budget_rss::expanded_uncertainty(combined, cfg.coverage_factor);
    let authorized =
        gate_operator::technician_authorized(&pack.technician, &pack.instrument_id, &pack.as_of_date);
    let raw_decisions = matrix_limits::channel_decisions(&readings);
    let decisions: Vec<ChannelDecision> = raw_decisions
        .into_iter()
        .map(|(channel, within, deviation)| ChannelDecision {
            channel,
            within_tolerance: within,
            deviation,
        })
        .collect();
    let oot = matrix_limits::oot_count(&readings);
    Ok(StagedInstrument {
        instrument_id: pack.instrument_id.clone(),
        cert_valid,
        cert_digest: digest,
        std_root,
        combined_uncertainty: combined,
        expanded_uncertainty: expanded,
        authorized_tech: authorized,
        decisions,
        out_of_tolerance_count: oot,
    })
}

fn parse_batch_pack(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut batch_id = String::new();
    let mut pack = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--batch" if i + 1 < args.len() => {
                batch_id = args[i + 1].clone();
                i += 2;
            }
            "--pack" if i + 1 < args.len() => {
                pack = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if batch_id.is_empty() || pack.is_empty() {
        eprintln!("--batch and --pack required");
        return Err(2);
    }
    Ok((batch_id, pack))
}

fn parse_batch(args: &[String], start: usize) -> Result<String, i32> {
    let mut batch_id = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--batch" if i + 1 < args.len() => {
                batch_id = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if batch_id.is_empty() {
        eprintln!("--batch required");
        return Err(2);
    }
    Ok(batch_id)
}

fn parse_batch_output(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut batch_id = String::new();
    let mut output = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--batch" if i + 1 < args.len() => {
                batch_id = args[i + 1].clone();
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
    if batch_id.is_empty() || output.is_empty() {
        eprintln!("--batch and --output required");
        return Err(2);
    }
    Ok((batch_id, output))
}
