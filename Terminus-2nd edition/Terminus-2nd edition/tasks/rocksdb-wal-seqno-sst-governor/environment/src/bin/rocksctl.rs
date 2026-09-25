use rocksdb_governor::{
    DEFAULT_CHECKSUM_PATH, DEFAULT_COMPACT_STATE_PATH, DEFAULT_GOVERNOR_PATH, DEFAULT_STAGE_PATH,
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
        "wal" => {
            if args.len() != 4 || args[2] != "ingest" {
                eprintln!("usage: rocksctl wal ingest <fixture-dir>");
                return Err(2);
            }
            rocksdb_governor::ingest::ingest_fixture_dir(&args[3], DEFAULT_STAGE_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "compact" => {
            if args.len() < 3 || args[2] != "plan" {
                eprintln!("usage: rocksctl compact plan export [--pass N]");
                return Err(2);
            }
            if args.len() < 4 || args[3] != "export" {
                eprintln!("usage: rocksctl compact plan export [--pass N]");
                return Err(2);
            }
            let mut pass = 1u32;
            if args.len() == 6 && args[4] == "--pass" {
                pass = args[5].parse().map_err(|_| {
                    eprintln!("bad --pass value");
                    2
                })?;
            } else if args.len() != 4 {
                eprintln!("usage: rocksctl compact plan export [--pass N]");
                return Err(2);
            }
            rocksdb_governor::export::compact_export(
                DEFAULT_STAGE_PATH,
                DEFAULT_GOVERNOR_PATH,
                DEFAULT_CHECKSUM_PATH,
                DEFAULT_COMPACT_STATE_PATH,
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
    eprintln!("usage: rocksctl wal ingest <fixture-dir> | rocksctl compact plan export [--pass N]");
}
