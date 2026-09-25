use lumidmx_audit::{
    DEFAULT_ATLAS_PATH, DEFAULT_DIGEST_PATH, DEFAULT_LEDGER_PATH, DEFAULT_STAGING_PATH,
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
        "demux" => parse_demux(&args),
        "atlas" => parse_atlas(&args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn parse_stage(args: &[String]) -> Result<(), i32> {
    if args.len() < 3 || args[2] != "ingest" {
        eprintln!("usage: lumidmx stage ingest --reads-dir DIR --manifest PATH --lanes PATH");
        return Err(2);
    }
    let mut reads_dir = String::new();
    let mut manifest = String::new();
    let mut lanes = String::new();
    let mut i = 3;
    while i < args.len() {
        match args[i].as_str() {
            "--reads-dir" if i + 1 < args.len() => {
                reads_dir = args[i + 1].clone();
                i += 2;
            }
            "--manifest" if i + 1 < args.len() => {
                manifest = args[i + 1].clone();
                i += 2;
            }
            "--lanes" if i + 1 < args.len() => {
                lanes = args[i + 1].clone();
                i += 2;
            }
            _ => {
                eprintln!("usage: lumidmx stage ingest --reads-dir DIR --manifest PATH --lanes PATH");
                return Err(2);
            }
        }
    }
    if reads_dir.is_empty() || manifest.is_empty() || lanes.is_empty() {
        eprintln!("stage ingest: --reads-dir, --manifest, and --lanes are required");
        return Err(2);
    }
    lumidmx_audit::stage::ingest::ingest_reads(
        &reads_dir,
        &manifest,
        &lanes,
        DEFAULT_STAGING_PATH,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn parse_demux(args: &[String]) -> Result<(), i32> {
    if args.len() != 3 || args[2] != "run" {
        eprintln!("usage: lumidmx demux run");
        return Err(2);
    }
    lumidmx_audit::demux::run::run_demux(DEFAULT_STAGING_PATH, DEFAULT_LEDGER_PATH).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn parse_atlas(args: &[String]) -> Result<(), i32> {
    if args.len() != 3 || args[2] != "export" {
        eprintln!("usage: lumidmx atlas export");
        return Err(2);
    }
    lumidmx_audit::export::atlas_export(
        DEFAULT_STAGING_PATH,
        DEFAULT_LEDGER_PATH,
        DEFAULT_ATLAS_PATH,
        DEFAULT_DIGEST_PATH,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!(
        "usage: lumidmx stage ingest --reads-dir DIR --manifest PATH --lanes PATH | lumidmx demux run | lumidmx atlas export"
    );
}
