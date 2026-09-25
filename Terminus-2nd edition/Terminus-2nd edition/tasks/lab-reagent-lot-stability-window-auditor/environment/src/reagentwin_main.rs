use lab_reagent_lot_stability::assay_coupling;
use lab_reagent_lot_stability::calendar_extend;
use lab_reagent_lot_stability::chrono_integral;
use lab_reagent_lot_stability::closure_emit;
use lab_reagent_lot_stability::correlation_store;
use lab_reagent_lot_stability::provenance_digest;
use lab_reagent_lot_stability::session_io;
use lab_reagent_lot_stability::win_schema::{Config, CorrelatedLot, LotRecord};
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
        "correlate" => run_correlate(&cfg, &args),
        "publish-closure" => run_publish_closure(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/reagentwin.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: reagentwin correlate|publish-closure ...");
}

fn correlation_path(cfg: &Config, session_id: &str) -> PathBuf {
    PathBuf::from(&cfg.correlation_dir).join(format!("{session_id}.json"))
}

fn run_correlate(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (session_id, bundle) = parse_session_bundle(args, 2)?;
    let path = session_io::bundle_path(&bundle);
    let bf = session_io::load_bundle(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let corr_path = correlation_path(cfg, &session_id);
    let prev = correlation_store::read_generation(corr_path.to_str().unwrap());
    let lots = correlate_lots(&bf).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    correlation_store::write_correlation(
        corr_path.to_str().unwrap(),
        &session_id,
        &bundle,
        &bf.as_of_date,
        prev,
        lots,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn correlate_lots(bf: &lab_reagent_lot_stability::win_schema::BundleFile) -> Result<Vec<CorrelatedLot>, String> {
    let lots_src: Vec<LotRecord> = bf.lots.clone();
    let mut out = Vec::new();
    for lot in &lots_src {
        let cert = provenance_digest::lot_cert_digest(
            &lot.lot_id,
            &bf.as_of_date,
            &lot.assay_code,
        );
        let tele = assay_coupling::telemetry_for_lot(&lot.lot_id, &bf.telemetry, &lots_src);
        let excursion = chrono_integral::excursion_minutes(&tele);
        let peak = tele.iter().map(|t| t.celsius).fold(0.0_f64, f64::max);
        let threshold = tele.first().map(|t| t.threshold_celsius).unwrap_or(8.0);
        let severity = chrono_integral::severity_score(excursion, peak, threshold);
        let extended = calendar_extend::extended_expiry(
            &lot.base_expiry,
            lot.cold_chain_days,
            lot.stability_bonus_days,
        )?;
        let quarantine = excursion > 0;
        out.push(CorrelatedLot {
            lot_id: lot.lot_id.clone(),
            assay_code: lot.assay_code.clone(),
            base_expiry: lot.base_expiry.clone(),
            cert_digest: cert,
            excursion_minutes: excursion,
            extended_expiry: extended,
            severity,
            quarantine,
        });
    }
    Ok(out)
}

fn run_publish_closure(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (session_id, output) = parse_session_output(args, 2)?;
    let corr_path = correlation_path(cfg, &session_id);
    let report = closure_emit::build_closure(corr_path.to_str().unwrap(), &session_id).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    closure_emit::write_closure(&PathBuf::from(output), &report).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn parse_session_bundle(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut session_id = String::new();
    let mut bundle = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--session" if i + 1 < args.len() => {
                session_id = args[i + 1].clone();
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
    if session_id.is_empty() || bundle.is_empty() {
        eprintln!("--session and --bundle required");
        return Err(2);
    }
    Ok((session_id, bundle))
}

fn parse_session_output(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut session_id = String::new();
    let mut output = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--session" if i + 1 < args.len() => {
                session_id = args[i + 1].clone();
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
    if session_id.is_empty() || output.is_empty() {
        eprintln!("--session and --output required");
        return Err(2);
    }
    Ok((session_id, output))
}
