use packctl::{DEFAULT_EXPORT_PATH, DEFAULT_STAGE_PATH};

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
        "ingest" => {
            if args.len() != 3 {
                eprintln!("usage: packctl ingest <pack-dir>");
                return Err(2);
            }
            packctl::ingest::ingest_directory(&args[2], DEFAULT_STAGE_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "resolve" => {
            if args.len() != 3 || args[2] != "export" {
                eprintln!("usage: packctl resolve export");
                return Err(2);
            }
            packctl::export::resolve_export(DEFAULT_STAGE_PATH, DEFAULT_EXPORT_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        _ => {
            usage();
            return Err(2);
        }
    }
    Ok(())
}

fn usage() {
    eprintln!("usage: packctl ingest <pack-dir> | packctl resolve export");
}
