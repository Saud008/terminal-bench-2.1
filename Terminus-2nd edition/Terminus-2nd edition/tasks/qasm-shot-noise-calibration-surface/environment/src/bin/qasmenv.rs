use qasm_env::{
    DEFAULT_DIGEST_PATH, DEFAULT_ENVELOPE_PATH, DEFAULT_LEDGER_PATH, DEFAULT_STAGING_PATH,
};

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
    match args[1].as_str() {
        "stage" => parse_stage(&args),
        "envelope" => parse_envelope(&args),
        "report" => parse_report(&args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn parse_stage(args: &[String]) -> Result<(), i32> {
    if args.len() < 3 || args[2] != "ingest" {
        eprintln!("usage: qasmenv stage ingest --cal-dir DIR --qasm PATH --manifest PATH");
        return Err(2);
    }
    let mut cal_dir = String::new();
    let mut qasm = String::new();
    let mut manifest = String::new();
    let mut i = 3;
    while i < args.len() {
        match args[i].as_str() {
            "--cal-dir" if i + 1 < args.len() => {
                cal_dir = args[i + 1].clone();
                i += 2;
            }
            "--qasm" if i + 1 < args.len() => {
                qasm = args[i + 1].clone();
                i += 2;
            }
            "--manifest" if i + 1 < args.len() => {
                manifest = args[i + 1].clone();
                i += 2;
            }
            _ => {
                eprintln!("usage: qasmenv stage ingest --cal-dir DIR --qasm PATH --manifest PATH");
                return Err(2);
            }
        }
    }
    if cal_dir.is_empty() || qasm.is_empty() || manifest.is_empty() {
        eprintln!("stage ingest: --cal-dir, --qasm, and --manifest are required");
        return Err(2);
    }
    qasm_env::stage::ingest::ingest_calibration(
        &cal_dir,
        &qasm,
        &manifest,
        DEFAULT_STAGING_PATH,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn parse_envelope(args: &[String]) -> Result<(), i32> {
    if args.len() != 3 || args[2] != "compute" {
        eprintln!("usage: qasmenv envelope compute");
        return Err(2);
    }
    qasm_env::envelope::compute::compute_envelope(DEFAULT_STAGING_PATH, DEFAULT_LEDGER_PATH).map_err(
        |e| {
            eprintln!("{e}");
            1
        },
    )
}

fn parse_report(args: &[String]) -> Result<(), i32> {
    if args.len() != 3 || args[2] != "export" {
        eprintln!("usage: qasmenv report export");
        return Err(2);
    }
    qasm_env::export::report::export_report(
        DEFAULT_LEDGER_PATH,
        DEFAULT_ENVELOPE_PATH,
        DEFAULT_DIGEST_PATH,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!(
        "usage: qasmenv stage ingest --cal-dir DIR --qasm PATH --manifest PATH | qasmenv envelope compute | qasmenv report export"
    );
}
