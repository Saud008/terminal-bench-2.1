use tuf_verify::{
    DEFAULT_REJECTED_PATH, DEFAULT_REPORT_PATH, DEFAULT_STAGING_PATH, DEFAULT_VERIFY_PATH,
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
        "ingest" => {
            if args.len() != 3 {
                eprintln!("usage: tufctl ingest <metadata-dir>");
                return Err(2);
            }
            tuf_verify::ingest::ingest_directory(&args[2], DEFAULT_STAGING_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "verify" => {
            if args.len() < 3 || args[2] != "rotation" {
                eprintln!("usage: tufctl verify rotation --epoch <n> [--staging <path>]");
                return Err(2);
            }
            let mut epoch: Option<u64> = None;
            let mut staging = DEFAULT_STAGING_PATH.to_string();
            let mut i = 3;
            while i < args.len() {
                match args[i].as_str() {
                    "--epoch" if i + 1 < args.len() => {
                        epoch = Some(args[i + 1].parse().map_err(|_| 2)?);
                        i += 2;
                    }
                    "--staging" if i + 1 < args.len() => {
                        staging = args[i + 1].clone();
                        i += 2;
                    }
                    _ => return Err(2),
                }
            }
            let Some(epoch) = epoch else {
                eprintln!("verify rotation: --epoch required");
                return Err(2);
            };
            tuf_verify::verify::verify_rotation(&staging, epoch, DEFAULT_VERIFY_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "export" => {
            if args.len() != 3 || args[2] != "report" {
                eprintln!("usage: tufctl export report");
                return Err(2);
            }
            tuf_verify::export::export_report(
                DEFAULT_STAGING_PATH,
                DEFAULT_VERIFY_PATH,
                DEFAULT_REPORT_PATH,
                DEFAULT_REJECTED_PATH,
            )
            .map_err(|e| {
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
    eprintln!("usage: tufctl ingest <dir> | tufctl verify rotation --epoch <n> | tufctl export report");
}
