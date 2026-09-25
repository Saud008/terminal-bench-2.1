use tantivy_merge::{
    DEFAULT_CHECKSUM_PATH, DEFAULT_MERGE_STATE_PATH, DEFAULT_STAGE_PATH, DEFAULT_STATS_PATH,
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
                eprintln!("usage: tantictl ingest <segments-dir>");
                return Err(2);
            }
            tantivy_merge::ingest::ingest_directory(&args[2], DEFAULT_STAGE_PATH)
                .map_err(|e| {
                    eprintln!("{e}");
                    1
                })?;
        }
        "merge" => {
            if args.len() < 3 || args[2] != "export" {
                eprintln!("usage: tantictl merge export [--pass N]");
                return Err(2);
            }
            let mut pass = 1u32;
            if args.len() == 5 && args[3] == "--pass" {
                pass = args[4].parse().map_err(|_| {
                    eprintln!("bad --pass value");
                    2
                })?;
            } else if args.len() != 3 {
                eprintln!("usage: tantictl merge export [--pass N]");
                return Err(2);
            }
            tantivy_merge::export::merge_export(
                DEFAULT_STAGE_PATH,
                DEFAULT_STATS_PATH,
                DEFAULT_CHECKSUM_PATH,
                DEFAULT_MERGE_STATE_PATH,
                pass,
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
    eprintln!("usage: tantictl ingest <segments-dir> | tantictl merge export [--pass N]");
}
